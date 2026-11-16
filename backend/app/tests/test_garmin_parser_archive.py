"""FIT parser and archive reader (Unit 2: activity-import)."""

import io
import zipfile
from datetime import datetime, timezone

import pytest
from app.core.exceptions import BadRequestError, PayloadTooLargeError
from app.modules.integrations.garmin.archive import (
    REASON_ARCHIVE_DAMAGED,
    REASON_ARCHIVE_TOO_BIG,
    REASON_ARCHIVE_TOO_MANY,
    REASON_ENTRY_TOO_BIG,
    ArchiveError,
    ArchiveLimits,
    iter_fit_entries,
)
from app.modules.integrations.garmin.fit_parser import (
    REASON_DAMAGED,
    REASON_TOO_LARGE,
    FitParseError,
    NotAnActivityError,
    parse_fit,
)
from app.modules.integrations.garmin.upload_validation import check_size, classify_upload
from app.tests.fit_support import FitSpec, build_fit, steady_samples
from hypothesis import given, settings
from hypothesis import strategies as st

LIMITS = {"max_messages": 1_000_000, "max_seconds": 20.0}
ROOMY = ArchiveLimits(max_entries=1000, max_total_bytes=10_000_000, max_entry_bytes=1_000_000)


def _run_fit(**changes) -> bytes:
    spec = FitSpec(distance_m=3000.0, timer_s=900.0, elapsed_s=930.0, samples=steady_samples(3000.0, 900.0), laps=2)
    for key, value in changes.items():
        setattr(spec, key, value)
    return build_fit(spec)


def _zip(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return buffer.getvalue()


# --- Parser ---------------------------------------------------------------------------------------


def test_parses_a_running_activity():
    parsed = parse_fit(_run_fit(), **LIMITS)

    assert parsed.source == "garmin" and parsed.sport == "running"
    assert parsed.external_id == f"fit:3412345678:{int(datetime(2026, 5, 3, 1, 0, tzinfo=timezone.utc).timestamp())}"
    assert parsed.start_time_utc == datetime(2026, 5, 3, 1, 0, tzinfo=timezone.utc)
    assert (parsed.distance_m, parsed.timer_s, parsed.elapsed_s) == (3000.0, 900.0, 930.0)
    assert (parsed.avg_hr, parsed.max_hr, parsed.calories, parsed.elevation_gain_m) == (150, 171, 210, 25.0)
    assert parsed.avg_cadence == 170.0  # FIT stores one leg: 85 -> 170 steps per minute
    assert (parsed.training_effect_aerobic, parsed.training_effect_anaerobic) == (3.4, 0.8)
    assert parsed.device and parsed.device.startswith("Garmin")
    assert [lap.index for lap in parsed.laps] == [1, 2]
    assert parsed.laps[1].start_offset_s == 465.0 and parsed.laps[0].distance_m == 1500.0

    series = parsed.series
    assert series is not None and len(series.time_s) == 61
    assert series.time_s[0] == 0 and series.time_s[-1] == 900
    assert series.distance_m[-1] == 3000.0
    assert series.cadence[0] == 168.0
    assert abs(series.lat[0] - 12.9716) < 1e-4 and abs(series.lon[0] - 77.5946) < 1e-4
    assert series.altitude_m[0] == 100.0 and series.heart_rate[0] == 140


@pytest.mark.parametrize(
    ("sport", "sub_sport", "expected"),
    [
        (1, 0, "running"),
        (1, 1, "treadmill_running"),
        (1, 3, "trail_running"),
        (1, 4, "track_running"),
        (1, 58, "virtual_running"),
        (2, 0, "cycling"),
        (11, 0, "walking"),
    ],
)
def test_sport_is_normalised(sport, sub_sport, expected):
    assert parse_fit(_run_fit(sport=sport, sub_sport=sub_sport), **LIMITS).sport == expected


def test_cycling_cadence_is_not_doubled():
    parsed = parse_fit(_run_fit(sport=2), **LIMITS)
    assert parsed.avg_cadence == 85.0 and parsed.series.cadence[0] == 84.0


def test_missing_optional_values_are_none_not_zero():
    spec = FitSpec(
        distance_m=1000.0, timer_s=300.0, elapsed_s=300.0, ascent_m=None, avg_hr=None, max_hr=None,
        calories=None, aerobic_te=None, anaerobic_te=None, avg_cadence=None,
    )
    parsed = parse_fit(build_fit(spec), **LIMITS)

    assert parsed.series is None
    assert (parsed.avg_hr, parsed.max_hr, parsed.calories, parsed.elevation_gain_m) == (None, None, None, None)
    assert (parsed.avg_cadence, parsed.training_effect_aerobic) == (None, None)


def test_indoor_activity_has_a_series_without_a_route():
    parsed = parse_fit(_run_fit(samples=steady_samples(3000.0, 900.0, with_gps=False)), **LIMITS)
    assert parsed.series.lat is None and parsed.series.lon is None and parsed.series.distance_m is not None


def test_external_id_falls_back_to_a_content_hash_without_a_serial_number():
    data = _run_fit(serial=None)
    first, second = parse_fit(data, **LIMITS), parse_fit(data, **LIMITS)
    other = parse_fit(_run_fit(serial=None, distance_m=3100.0), **LIMITS)

    assert first.external_id.startswith("sha256:") and first.external_id == second.external_id
    assert other.external_id != first.external_id


def test_a_file_that_is_not_an_activity_is_recognised():
    with pytest.raises(NotAnActivityError):
        parse_fit(_run_fit(file_type=2), **LIMITS)  # device settings
    with pytest.raises(NotAnActivityError):
        parse_fit(_run_fit(include_session=False), **LIMITS)


def test_damaged_files_fail_with_a_fixed_reason():
    good = _run_fit()
    corrupted = bytearray(good)
    corrupted[40] ^= 0xFF  # inside the body: CRC no longer matches
    for broken in (good[: len(good) // 2], bytes(corrupted), good[:14], b"\x0e\x20" + b"garbage" * 5):
        with pytest.raises(FitParseError) as caught:
            parse_fit(broken, **LIMITS)
        assert caught.value.reason == REASON_DAMAGED
        assert "fitdecode" not in caught.value.reason


def test_message_budget_is_enforced():
    with pytest.raises(FitParseError) as caught:
        parse_fit(_run_fit(), max_messages=5, max_seconds=20.0)
    assert caught.value.reason == REASON_TOO_LARGE


def test_time_budget_is_enforced():
    big = _run_fit(samples=steady_samples(3000.0, 900.0, count=2500))
    with pytest.raises(FitParseError) as caught:
        parse_fit(big, max_messages=1_000_000, max_seconds=0.0)
    assert caught.value.reason == REASON_TOO_LARGE


# --- Upload classification ------------------------------------------------------------------------


def test_uploads_are_classified_by_content_not_name():
    assert classify_upload(_run_fit()[:16]) == "fit"
    assert classify_upload(_zip({"a.fit": b"x"})[:16]) == "zip"
    for head in (b"hello, world!!!!!", b"", b"\x89PNG\r\n\x1a\n" + bytes(8)):
        with pytest.raises(BadRequestError):
            classify_upload(head)


def test_size_limits_depend_on_kind():
    class Limits:
        garmin_import_max_fit_bytes = 100
        garmin_import_max_archive_bytes = 1000

    check_size("fit", 100, Limits())
    check_size("zip", 1000, Limits())
    with pytest.raises(PayloadTooLargeError):
        check_size("fit", 101, Limits())
    with pytest.raises(PayloadTooLargeError):
        check_size("zip", 1001, Limits())


# --- Archives -------------------------------------------------------------------------------------


def test_archive_yields_fit_entries_and_one_nested_level_only():
    inner = _zip({"deep/run2.fit": b"two"})
    innermost = _zip({"too/deep.fit": b"never"})
    outer = _zip(
        {
            "DI_CONNECT/uploads/run1.fit": b"one",
            "DI_CONNECT/uploads/Part1.zip": _zip({"run3.fit": b"three", "again.zip": innermost}),
            "other.zip": inner,
            "notes.txt": b"ignored",
            "dir/": b"",
        }
    )

    entries = list(iter_fit_entries(io.BytesIO(outer), ROOMY))

    assert sorted((e.name, e.data) for e in entries) == [
        ("run1.fit", b"one"),
        ("run2.fit", b"two"),
        ("run3.fit", b"three"),
    ]


def test_entry_names_are_labels_only_and_are_sanitised():
    entries = list(iter_fit_entries(io.BytesIO(_zip({"../../evil\x07name.FIT": b"x"})), ROOMY))
    assert [e.name for e in entries] == ["evilname.FIT"]


def test_a_damaged_archive_is_rejected_with_a_fixed_reason():
    with pytest.raises(ArchiveError) as caught:
        list(iter_fit_entries(io.BytesIO(b"PK\x03\x04 not really a zip"), ROOMY))
    assert caught.value.reason == REASON_ARCHIVE_DAMAGED


def test_too_many_entries_reject_the_archive_before_reading_anything():
    archive = _zip({f"f{i}.fit": b"x" for i in range(5)})
    with pytest.raises(ArchiveError) as caught:
        list(iter_fit_entries(io.BytesIO(archive), ArchiveLimits(4, 10_000, 1000)))
    assert caught.value.reason == REASON_ARCHIVE_TOO_MANY


def test_an_oversized_entry_is_reported_and_the_rest_continue():
    archive = _zip({"huge.fit": b"x" * 5000, "small.fit": b"ok"})
    entries = list(iter_fit_entries(io.BytesIO(archive), ArchiveLimits(10, 100_000, 1000)))

    assert [(e.name, e.data, e.problem) for e in entries] == [
        ("huge.fit", None, REASON_ENTRY_TOO_BIG),
        ("small.fit", b"ok", None),
    ]


def test_expansion_beyond_the_total_budget_stops_the_archive():
    archive = _zip({f"f{i}.fit": b"a" * 600 for i in range(5)})
    with pytest.raises(ArchiveError) as caught:
        list(iter_fit_entries(io.BytesIO(archive), ArchiveLimits(100, 1500, 1000)))
    assert caught.value.reason == REASON_ARCHIVE_TOO_BIG


def test_a_zip_bomb_is_cut_off_by_the_bounded_read():
    bomb = _zip({"bomb.fit": bytes(20_000_000)})  # compresses to a few KB
    assert len(bomb) < 100_000
    entries = list(iter_fit_entries(io.BytesIO(bomb), ArchiveLimits(10, 50_000_000, 1_000_000)))
    assert [(e.data, e.problem) for e in entries] == [(None, REASON_ENTRY_TOO_BIG)]


@given(
    sizes=st.lists(st.integers(min_value=0, max_value=400), min_size=0, max_size=12),
    max_entries=st.integers(min_value=1, max_value=14),
    max_total=st.integers(min_value=1, max_value=3000),
    max_entry=st.integers(min_value=1, max_value=500),
)
@settings(max_examples=80, deadline=None)
def test_archive_reading_never_exceeds_the_limits(sizes, max_entries, max_total, max_entry):
    archive = _zip({f"f{i}.fit": b"z" * size for i, size in enumerate(sizes)})
    limits = ArchiveLimits(max_entries, max_total, max_entry)
    yielded_bytes, yielded = 0, 0
    try:
        for entry in iter_fit_entries(io.BytesIO(archive), limits):
            yielded += 1
            if entry.data is not None:
                assert len(entry.data) <= max_entry
                yielded_bytes += len(entry.data)
    except ArchiveError:
        pass
    assert yielded <= max_entries
    assert yielded_bytes <= max_total

