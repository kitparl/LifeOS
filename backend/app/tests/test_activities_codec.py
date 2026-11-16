"""Activity codec: route polyline, series packing, per-km splits, downsampling (Unit 2: activity-import)."""

from app.modules.activities.contracts import ParsedSeries
from app.modules.activities.splits import (
    MIN_PARTIAL_SPLIT_M,
    compute_km_splits,
    decode_polyline,
    downsample_indices,
    encode_polyline,
    pack_series,
    route_points,
    unpack_series,
)
from hypothesis import given, settings
from hypothesis import strategies as st

# --- Generators (PBT-07: shaped like real activity data) ------------------------------------------

latitude = st.floats(min_value=-89.9, max_value=89.9, allow_nan=False).map(lambda v: round(v, 5))
longitude = st.floats(min_value=-179.9, max_value=179.9, allow_nan=False).map(lambda v: round(v, 5))
route = st.lists(st.tuples(latitude, longitude), max_size=40)


@st.composite
def series_with_distance(draw, max_samples: int = 60) -> ParsedSeries:
    """A run: strictly increasing time, non-decreasing distance, optional channels."""
    count = draw(st.integers(min_value=2, max_value=max_samples))
    gaps = draw(st.lists(st.integers(min_value=1, max_value=20), min_size=count, max_size=count))
    steps = draw(st.lists(st.floats(min_value=0.0, max_value=120.0, allow_nan=False), min_size=count, max_size=count))
    time_s, distance, t, d = [], [], 0, 0.0
    for gap, step in zip(gaps, steps, strict=True):
        t += gap
        d += step
        time_s.append(t)
        distance.append(round(d, 2))
    with_hr = draw(st.booleans())
    return ParsedSeries(
        time_s=time_s,
        distance_m=distance,
        heart_rate=[100 + i % 60 for i in range(count)] if with_hr else None,
        altitude_m=[50.0 + (i % 7) for i in range(count)],
        cadence=[170.0 + i % 4 for i in range(count)],
    )


# --- Polyline -------------------------------------------------------------------------------------


def test_polyline_matches_the_documented_reference_example():
    points = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
    assert encode_polyline(points) == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    assert decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@") == points


def test_empty_route_encodes_to_nothing():
    assert encode_polyline([]) == ""
    assert decode_polyline("") == []


@given(points=route)
@settings(max_examples=200)
def test_polyline_round_trip(points):
    decoded = decode_polyline(encode_polyline(points))
    assert len(decoded) == len(points)
    for (lat, lon), (dlat, dlon) in zip(points, decoded, strict=True):
        assert abs(lat - dlat) < 1e-5 and abs(lon - dlon) < 1e-5


# --- Series packing -------------------------------------------------------------------------------


@given(series=series_with_distance())
@settings(max_examples=100)
def test_series_pack_round_trip(series):
    assert unpack_series(pack_series(series)) == series


def test_series_with_gaps_and_extras_round_trips():
    series = ParsedSeries(
        time_s=[1, 2, 3],
        distance_m=[0.0, None, 5.5],
        lat=[1.5, None, 1.6],
        lon=[2.5, None, 2.6],
        heart_rate=[None, 150, 151],
        extras={"power": [200.0, None, 210.0]},
    )
    assert unpack_series(pack_series(series)) == series


# --- Downsampling ---------------------------------------------------------------------------------


@given(count=st.integers(min_value=0, max_value=5000), limit=st.integers(min_value=1, max_value=700))
@settings(max_examples=200)
def test_downsample_never_exceeds_limit_and_keeps_both_ends(count, limit):
    indices = downsample_indices(count, limit)
    assert len(indices) <= limit
    assert indices == sorted(set(indices))
    if count:
        assert indices[0] == 0
        if limit > 1:
            assert indices[-1] == count - 1
    else:
        assert indices == []


def test_route_points_skips_samples_without_position_and_respects_limit():
    series = ParsedSeries(
        time_s=list(range(6)),
        lat=[1.0, None, 3.0, 4.0, 5.0, 6.0],
        lon=[1.0, 2.0, None, 4.0, 5.0, 6.0],
    )
    assert route_points(series, 100) == [(1.0, 1.0), (4.0, 4.0), (5.0, 5.0), (6.0, 6.0)]
    assert len(route_points(series, 2)) == 2
    assert route_points(ParsedSeries(time_s=[1, 2]), 10) == []


# --- Splits ---------------------------------------------------------------------------------------


def _steady(distance_m: float, seconds: int, samples: int) -> ParsedSeries:
    return ParsedSeries(
        time_s=[round(seconds * i / samples) for i in range(samples + 1)],
        distance_m=[distance_m * i / samples for i in range(samples + 1)],
        heart_rate=[140 + i % 10 for i in range(samples + 1)],
        altitude_m=[100.0 + i for i in range(samples + 1)],
        cadence=[170.0] * (samples + 1),
    )


def test_ten_point_four_km_gives_ten_full_splits_and_a_partial_one():
    splits = compute_km_splits(_steady(10_400, 3120, 104))

    assert [s.index for s in splits] == list(range(1, 12))
    assert [s.distance_m for s in splits[:10]] == [1000.0] * 10
    assert abs(splits[10].distance_m - 400.0) < 1e-6
    assert all(abs(s.pace_s_per_km - 300.0) < 1.0 for s in splits)
    assert splits[0].avg_hr is not None and splits[0].avg_cadence == 170.0
    assert splits[0].elevation_change_m is not None and splits[0].elevation_change_m > 0


def test_remainder_below_the_minimum_is_not_reported():
    splits = compute_km_splits(_steady(2000 + MIN_PARTIAL_SPLIT_M - 1, 600, 80))
    assert [s.index for s in splits] == [1, 2]


def test_no_distance_channel_or_too_few_samples_means_no_splits():
    assert compute_km_splits(ParsedSeries(time_s=[1, 2, 3])) == []
    assert compute_km_splits(ParsedSeries(time_s=[1], distance_m=[0.0])) == []


def test_missing_heart_rate_and_altitude_give_none_not_zero():
    series = ParsedSeries(time_s=[0, 100, 200, 300], distance_m=[0.0, 500.0, 1000.0, 1500.0])
    first = compute_km_splits(series)[0]
    assert first.avg_hr is None and first.elevation_change_m is None and first.avg_cadence is None


@given(series=series_with_distance())
@settings(max_examples=150)
def test_split_distances_and_durations_account_for_the_recorded_distance(series):
    splits = compute_km_splits(series)
    total = max(d for d in series.distance_m if d is not None)

    assert all(s.distance_m == 1000.0 for s in splits[:-1])
    if splits:
        assert 0 < splits[-1].distance_m <= 1000.0
    covered = sum(s.distance_m for s in splits)
    assert covered <= total + 1e-6
    assert total - covered < MIN_PARTIAL_SPLIT_M + 1e-6 or not splits
    assert all(s.duration_s >= 0 for s in splits)
    assert all(s.pace_s_per_km is None or s.pace_s_per_km > 0 for s in splits)
    # splits tile the activity: their durations add up to the time between the first and last boundary
    assert sum(s.duration_s for s in splits) <= series.time_s[-1] + 1e-6

