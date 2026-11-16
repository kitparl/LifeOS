"""A minimal FIT file writer for tests (activity files only).

Writes just enough of the FIT protocol (header, definition and data messages, CRC-16) to produce
files the importer can parse, so tests need no third-party files, encoder library or network.
"""

import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone

# FIT epoch is 1989-12-31 00:00:00 UTC.
_FIT_EPOCH = datetime(1989, 12, 31, tzinfo=timezone.utc)

# base type name -> (code, struct format, invalid value)
_TYPES = {
    "enum": (0x00, "B", 0xFF),
    "uint8": (0x02, "B", 0xFF),
    "uint16": (0x84, "H", 0xFFFF),
    "sint32": (0x85, "i", 0x7FFFFFFF),
    "uint32": (0x86, "I", 0xFFFFFFFF),
    "uint32z": (0x8C, "I", 0),
}

_CRC_TABLE = [
    0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
    0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400,
]


def fit_crc(data: bytes, crc: int = 0) -> int:
    for byte in data:
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[byte & 0xF]
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[(byte >> 4) & 0xF]
    return crc


def fit_time(moment: datetime) -> int:
    return int((moment - _FIT_EPOCH).total_seconds())


def semicircles(degrees: float) -> int:
    return round(degrees * (2**31) / 180.0)


class _Writer:
    def __init__(self) -> None:
        self.body = bytearray()

    def message(self, local: int, global_num: int, fields: list[tuple[int, str, int | None]]) -> None:
        """fields: (field number, base type, value). None writes the type's 'invalid' value."""
        definition = bytearray([0x40 | local, 0, 0])  # definition header, reserved, little endian
        definition += struct.pack("<HB", global_num, len(fields))
        for number, kind, _ in fields:
            code, fmt, _ = _TYPES[kind]
            definition += bytes([number, struct.calcsize("<" + fmt), code])
        self.body += definition
        data = bytearray([local])
        for _, kind, value in fields:
            _, fmt, invalid = _TYPES[kind]
            data += struct.pack("<" + fmt, invalid if value is None else value)
        self.body += data

    def file_bytes(self) -> bytes:
        header = bytearray([14, 0x20]) + struct.pack("<HI", 2132, len(self.body)) + b".FIT"
        header += struct.pack("<H", fit_crc(bytes(header)))
        content = bytes(header) + bytes(self.body)
        return content + struct.pack("<H", fit_crc(content))


@dataclass
class Sample:
    seconds: int  # offset from start
    distance_m: float
    heart_rate: int | None = 150
    cadence: int | None = 85  # one leg, as FIT stores running cadence
    altitude_m: float | None = 100.0
    speed_mps: float | None = 3.3
    lat: float | None = None
    lon: float | None = None


@dataclass
class FitSpec:
    start: datetime = datetime(2026, 5, 3, 1, 0, tzinfo=timezone.utc)
    sport: int = 1  # 1 = running, 2 = cycling, 11 = walking
    sub_sport: int = 0  # 0 generic, 1 treadmill, 3 trail, 4 track, 58 virtual_activity
    file_type: int = 4  # 4 = activity
    serial: int | None = 3412345678
    time_created: datetime | None = None
    distance_m: float = 3000.0
    timer_s: float = 900.0
    elapsed_s: float = 930.0
    ascent_m: int | None = 25
    avg_hr: int | None = 150
    max_hr: int | None = 171
    avg_cadence: int | None = 85
    calories: int | None = 210
    aerobic_te: float | None = 3.4
    anaerobic_te: float | None = 0.8
    samples: list[Sample] = field(default_factory=list)
    laps: int = 1
    include_session: bool = True


def steady_samples(distance_m: float, timer_s: float, *, count: int = 60, with_gps: bool = True) -> list[Sample]:
    """Evenly paced samples from 0 to the full distance and time, with a small altitude wave and a straight route."""
    out = []
    for i in range(count + 1):
        frac = i / count
        out.append(
            Sample(
                seconds=round(timer_s * frac),
                distance_m=distance_m * frac,
                heart_rate=140 + round(20 * frac),
                cadence=84 + (i % 3),
                altitude_m=100.0 + 10 * (i % 5),
                speed_mps=distance_m / timer_s,
                lat=12.9716 + 0.0005 * i if with_gps else None,
                lon=77.5946 + 0.0005 * i if with_gps else None,
            )
        )
    return out


def build_fit(spec: FitSpec | None = None) -> bytes:
    spec = spec or FitSpec()
    created = spec.time_created or spec.start
    w = _Writer()
    w.message(0, 0, [
        (0, "enum", spec.file_type),
        (1, "uint16", 1),  # manufacturer: garmin
        (2, "uint16", 3990),  # product
        (3, "uint32z", spec.serial),
        (4, "uint32", fit_time(created)),
    ])
    samples = spec.samples
    if samples:
        for s in samples:
            w.message(1, 20, [
                (253, "uint32", fit_time(spec.start) + s.seconds),
                (0, "sint32", None if s.lat is None else semicircles(s.lat)),
                (1, "sint32", None if s.lon is None else semicircles(s.lon)),
                (2, "uint16", None if s.altitude_m is None else round((s.altitude_m + 500) * 5)),
                (3, "uint8", s.heart_rate),
                (4, "uint8", s.cadence),
                (5, "uint32", round(s.distance_m * 100)),
                (6, "uint16", None if s.speed_mps is None else round(s.speed_mps * 1000)),
            ])
    for lap in range(spec.laps):
        share = 1 / spec.laps
        w.message(2, 19, [
            (253, "uint32", fit_time(spec.start) + round(spec.elapsed_s * (lap + 1) * share)),
            (2, "uint32", fit_time(spec.start) + round(spec.elapsed_s * lap * share)),
            (7, "uint32", round(spec.elapsed_s * share * 1000)),
            (8, "uint32", round(spec.timer_s * share * 1000)),
            (9, "uint32", round(spec.distance_m * share * 100)),
            (15, "uint8", spec.avg_hr),
            (17, "uint8", spec.avg_cadence),
            (21, "uint16", spec.ascent_m),
        ])
    if spec.include_session:
        w.message(3, 18, [
            (253, "uint32", fit_time(spec.start) + round(spec.elapsed_s)),
            (2, "uint32", fit_time(spec.start)),
            (5, "enum", spec.sport),
            (6, "enum", spec.sub_sport),
            (7, "uint32", round(spec.elapsed_s * 1000)),
            (8, "uint32", round(spec.timer_s * 1000)),
            (9, "uint32", round(spec.distance_m * 100)),
            (11, "uint16", spec.calories),
            (16, "uint8", spec.avg_hr),
            (17, "uint8", spec.max_hr),
            (18, "uint8", spec.avg_cadence),
            (22, "uint16", spec.ascent_m),
            (24, "uint8", None if spec.aerobic_te is None else round(spec.aerobic_te * 10)),
            (137, "uint8", None if spec.anaerobic_te is None else round(spec.anaerobic_te * 10)),
        ])
    return w.file_bytes()
