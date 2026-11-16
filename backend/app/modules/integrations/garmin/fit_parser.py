"""Bounded parser for Garmin .FIT activity files.

Input is untrusted. All decoder failures are mapped to fixed, user-safe reasons; library messages
never leave this module.
"""

import hashlib
import io
import math
import time
from datetime import datetime, timezone

import fitdecode

from app.modules.activities.contracts import ParsedActivity, ParsedLap, ParsedSeries

SOURCE = "garmin"

REASON_DAMAGED = "File is damaged or incomplete"
REASON_TOO_LARGE = "File is too large to process"
REASON_UNREADABLE = "Could not read activity data"

_SEMICIRCLES_TO_DEGREES = 180.0 / 2**31
_CHECK_EVERY = 1000  # frames between deadline checks


class FitParseError(Exception):
    """The file cannot be imported. `reason` is a fixed, user-safe sentence."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class NotAnActivityError(FitParseError):
    """A valid FIT file that is not an activity (device settings, monitoring data, ...)."""

    def __init__(self) -> None:
        super().__init__("Not an activity file")


def _normalise_sport(sport: str | None, sub_sport: str | None) -> str:
    sport = (sport or "other").lower()
    if sport == "running":
        return {
            "trail": "trail_running",
            "treadmill": "treadmill_running",
            "track": "track_running",
            "virtual_activity": "virtual_running",
        }.get((sub_sport or "").lower(), "running")
    return sport[:32]


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _number(frame, *names: str) -> float | None:
    """First of the named fields that holds a finite number."""
    for name in names:
        if frame.has_field(name):
            value = frame.get_value(name, fallback=None)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                return float(value)
    return None


def _text(frame, name: str) -> str | None:
    if frame.has_field(name):
        value = frame.get_value(name, fallback=None)
        if isinstance(value, str) and value:
            return value
    return None


def _int(value: float | None) -> int | None:
    return None if value is None else round(value)


def _cadence_factor(running: bool) -> int:
    # FIT stores running cadence per leg; steps per minute is twice that.
    return 2 if running else 1


def _device_name(file_id) -> str | None:
    product = _text(file_id, "garmin_product") or (
        str(_number(file_id, "product")) if file_id.has_field("product") and _number(file_id, "product") else None
    )
    maker = _text(file_id, "manufacturer")
    parts = [p.replace("_", " ") for p in (maker.title() if maker else None, product) if p]
    return " ".join(parts)[:64] or None


def _external_id(file_id, data: bytes) -> str:
    serial = _number(file_id, "serial_number")
    created = _aware(file_id.get_value("time_created", fallback=None)) if file_id.has_field("time_created") else None
    if serial and created:
        return f"fit:{int(serial)}:{int(created.timestamp())}"
    return "sha256:" + hashlib.sha256(data).hexdigest()[:32]


def parse_fit(data: bytes, *, max_messages: int, max_seconds: float) -> ParsedActivity:
    """Decode one activity file within a message and time budget."""
    deadline = time.monotonic() + max_seconds
    file_id = session = None
    records, laps = [], []
    try:
        with fitdecode.FitReader(
            io.BytesIO(data),
            check_crc=fitdecode.CrcCheck.RAISE,
            error_handling=fitdecode.ErrorHandling.RAISE,
        ) as reader:
            for count, frame in enumerate(reader, start=1):
                if count > max_messages or (count % _CHECK_EVERY == 0 and time.monotonic() > deadline):
                    raise FitParseError(REASON_TOO_LARGE)
                if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                    continue
                if frame.name == "file_id" and file_id is None:
                    file_id = frame
                elif frame.name == "session" and session is None:
                    session = frame
                elif frame.name == "lap":
                    laps.append(frame)
                elif frame.name == "record":
                    records.append(frame)
    except FitParseError:
        raise
    except Exception as exc:  # noqa: BLE001 - one boundary for every decoder failure on untrusted bytes
        raise FitParseError(REASON_DAMAGED) from exc

    if file_id is None or session is None or _text(file_id, "type") != "activity":
        raise NotAnActivityError()

    start = _aware(session.get_value("start_time", fallback=None)) if session.has_field("start_time") else None
    if start is None and records:
        start = next((_aware(r.get_value("timestamp", fallback=None)) for r in records if r.has_field("timestamp")), None)
    if start is None and file_id.has_field("time_created"):
        start = _aware(file_id.get_value("time_created", fallback=None))
    if start is None:
        raise FitParseError(REASON_UNREADABLE)

    sport = _normalise_sport(_text(session, "sport"), _text(session, "sub_sport"))
    running = sport.endswith("running") or sport == "running"
    factor = _cadence_factor(running)

    series = _build_series(records, start, factor)
    distance = _number(session, "total_distance")
    if distance is None and series and series.distance_m:
        distance = next((d for d in reversed(series.distance_m) if d is not None), None)
    elapsed = _number(session, "total_elapsed_time")
    timer = _number(session, "total_timer_time") or elapsed
    if distance is None or elapsed is None or timer is None:
        raise FitParseError(REASON_UNREADABLE)

    avg_cadence = _number(session, "avg_running_cadence", "avg_cadence")
    training_aerobic = _number(session, "total_training_effect")
    training_anaerobic = _number(session, "total_anaerobic_training_effect")
    return ParsedActivity(
        source=SOURCE,
        external_id=_external_id(file_id, data),
        sport=sport,
        start_time_utc=start,
        elapsed_s=elapsed,
        timer_s=timer,
        distance_m=distance,
        elevation_gain_m=_number(session, "total_ascent"),
        avg_hr=_int(_number(session, "avg_heart_rate")),
        max_hr=_int(_number(session, "max_heart_rate")),
        avg_cadence=None if avg_cadence is None else avg_cadence * factor,
        max_speed_mps=_number(session, "enhanced_max_speed", "max_speed"),
        calories=_int(_number(session, "total_calories")),
        device=_device_name(file_id),
        training_effect_aerobic=None if training_aerobic is None else round(training_aerobic, 1),
        training_effect_anaerobic=None if training_anaerobic is None else round(training_anaerobic, 1),
        laps=_build_laps(laps, start, factor),
        series=series,
    )


def _build_laps(frames, start: datetime, factor: int) -> list[ParsedLap]:
    out = []
    for index, lap in enumerate(frames, start=1):
        lap_start = _aware(lap.get_value("start_time", fallback=None)) if lap.has_field("start_time") else None
        elapsed = _number(lap, "total_elapsed_time")
        duration = _number(lap, "total_timer_time") or elapsed
        distance = _number(lap, "total_distance")
        if duration is None or distance is None:
            continue
        cadence = _number(lap, "avg_running_cadence", "avg_cadence")
        out.append(
            ParsedLap(
                index=index,
                start_offset_s=max(0.0, (lap_start - start).total_seconds()) if lap_start else 0.0,
                duration_s=duration,
                distance_m=distance,
                avg_hr=_int(_number(lap, "avg_heart_rate")),
                avg_cadence=None if cadence is None else cadence * factor,
                elevation_gain_m=_number(lap, "total_ascent"),
            )
        )
    return out


def _valid_position(lat: float | None, lon: float | None) -> tuple[float | None, float | None]:
    if lat is None or lon is None:
        return None, None
    lat, lon = lat * _SEMICIRCLES_TO_DEGREES, lon * _SEMICIRCLES_TO_DEGREES
    if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
        return lat, lon
    return None, None


def _build_series(frames, start: datetime, factor: int) -> ParsedSeries | None:
    times: list[int] = []
    channels: dict[str, list] = {k: [] for k in ("distance_m", "lat", "lon", "altitude_m", "heart_rate", "cadence", "speed_mps")}
    for frame in frames:
        stamp = _aware(frame.get_value("timestamp", fallback=None)) if frame.has_field("timestamp") else None
        if stamp is None:
            continue
        times.append(max(0, int((stamp - start).total_seconds())))
        lat, lon = _valid_position(_number(frame, "position_lat"), _number(frame, "position_long"))
        cadence = _number(frame, "cadence")
        heart_rate = _number(frame, "heart_rate")
        channels["distance_m"].append(_number(frame, "distance"))
        channels["lat"].append(lat)
        channels["lon"].append(lon)
        channels["altitude_m"].append(_number(frame, "enhanced_altitude", "altitude"))
        channels["heart_rate"].append(_int(heart_rate))
        channels["cadence"].append(None if cadence is None else cadence * factor)
        channels["speed_mps"].append(_number(frame, "enhanced_speed", "speed"))
    if not times:
        return None
    present = {name: values for name, values in channels.items() if any(v is not None for v in values)}
    return ParsedSeries(time_s=times, **{name: present.get(name) for name in channels})
