"""Bounded reading of Garmin export archives (zip, with one level of nested zips).

Entries are read into memory one at a time. Entry names are labels only: nothing is ever written
to disk under an archive-supplied name, so path traversal names cannot do anything.
"""

import io
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

REASON_ARCHIVE_DAMAGED = "Archive is damaged or not a zip file"
REASON_ARCHIVE_TOO_MANY = "Archive has too many files"
REASON_ARCHIVE_TOO_BIG = "Archive is too large once unpacked"
REASON_ENTRY_TOO_BIG = "File is too large to process"
REASON_ENTRY_UNREADABLE = "File could not be read from the archive"


class ArchiveError(Exception):
    """The whole archive is rejected; `reason` is a fixed, user-safe sentence."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ArchiveLimits:
    max_entries: int
    max_total_bytes: int
    max_entry_bytes: int


@dataclass
class ArchiveBudget:
    """Counters shared by an archive and its nested archives."""

    entries: int = 0
    total_bytes: int = 0


@dataclass(frozen=True)
class ArchiveEntry:
    name: str  # base name only, for messages
    data: bytes | None  # None when the entry could not be used; see `problem`
    problem: str | None = None


def _label(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return "".join(ch for ch in base if ch.isprintable())[:80] or "file"


def _read_bounded(archive: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes | None:
    """Entry bytes, or None when the entry holds more than `limit` bytes (declared sizes are not trusted)."""
    with archive.open(info) as handle:
        data = handle.read(limit + 1)
    return None if len(data) > limit else data


def iter_fit_entries(
    source: str | Path | BinaryIO, limits: ArchiveLimits, budget: ArchiveBudget | None = None, depth: int = 0
) -> Iterator[ArchiveEntry]:
    """Yield every `.fit` entry of the archive and, at depth 0, of the zip archives inside it."""
    budget = budget or ArchiveBudget()
    try:
        archive = zipfile.ZipFile(source)
    except (zipfile.BadZipFile, OSError, ValueError, NotImplementedError) as exc:
        raise ArchiveError(REASON_ARCHIVE_DAMAGED) from exc
    with archive:
        infos = archive.infolist()
        budget.entries += len(infos)
        if budget.entries > limits.max_entries:
            raise ArchiveError(REASON_ARCHIVE_TOO_MANY)
        for info in infos:
            lowered = info.filename.lower()
            nested = depth == 0 and lowered.endswith(".zip")
            if info.is_dir() or not (lowered.endswith(".fit") or nested):
                continue
            label = _label(info.filename)
            try:
                data = _read_bounded(archive, info, limits.max_entry_bytes)
            except Exception:  # noqa: BLE001 - encrypted, truncated or corrupt entry: report it and move on
                yield ArchiveEntry(label, None, REASON_ENTRY_UNREADABLE)
                continue
            if data is None:
                yield ArchiveEntry(label, None, REASON_ENTRY_TOO_BIG)
                continue
            budget.total_bytes += len(data)
            if budget.total_bytes > limits.max_total_bytes:
                raise ArchiveError(REASON_ARCHIVE_TOO_BIG)
            if nested:
                try:
                    yield from iter_fit_entries(io.BytesIO(data), limits, budget, depth=1)
                except ArchiveError as exc:
                    if exc.reason in (REASON_ARCHIVE_TOO_MANY, REASON_ARCHIVE_TOO_BIG):
                        raise
                    yield ArchiveEntry(label, None, exc.reason)
            else:
                yield ArchiveEntry(label, data)
