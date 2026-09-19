from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Conversion failed (soffice missing, bad input, non-zero exit)."""


class ConversionTimeoutError(ConversionError):
    """Conversion exceeded the configured timeout."""


def soffice_available() -> bool:
    return shutil.which("soffice") is not None


async def convert_to_pdf(input_path: Path, *, timeout_seconds: int) -> bytes:
    """Convert `input_path` to PDF via headless LibreOffice, returning the PDF bytes.

    Security: argument-list subprocess (no shell), a fresh temp dir and a
    separate -env:UserInstallation profile per conversion, macros disabled by
    LibreOffice's own --headless mode, temp files always cleaned up. Never
    executes the input — LibreOffice only ever renders/converts it.
    """
    if not soffice_available():
        raise ConversionError("LibreOffice (soffice) is not installed on this host")

    with tempfile.TemporaryDirectory(prefix="docpreview_") as tmp_dir:
        tmp = Path(tmp_dir)
        profile_dir = tmp / "profile"
        outdir = tmp / "out"
        outdir.mkdir()

        args = [
            "soffice",
            "--headless",
            "--norestore",
            "--nologo",
            "--nofirststartwizard",
            f"-env:UserInstallation=file://{profile_dir}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(outdir),
            str(input_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise ConversionTimeoutError(
                f"Conversion exceeded {timeout_seconds}s"
            ) from exc

        if proc.returncode != 0:
            # Never include file contents/paths — stderr from soffice can be verbose.
            logger.warning("soffice exited %s: %s", proc.returncode, stderr[:2000].decode(errors="replace"))
            raise ConversionError("Document conversion failed")

        produced = list(outdir.glob("*.pdf"))
        if not produced:
            logger.warning("soffice produced no PDF output: %s", stdout[:2000].decode(errors="replace"))
            raise ConversionError("Document conversion produced no output")

        return produced[0].read_bytes()
