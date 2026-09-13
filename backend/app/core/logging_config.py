"""Central logging configuration for the LifeOS API."""

from __future__ import annotations

import logging
import sys


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure root logging once at app startup. Idempotent for basicConfig."""
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
    )
