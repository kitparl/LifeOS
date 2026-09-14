"""Central logging configuration for the LifeOS API."""

from __future__ import annotations

import logging
import sys

# Third-party loggers that are too chatty at DEBUG, or that leak secrets.
# httpx logs each request's full URL at INFO, and for the Telegram API that URL
# embeds the bot token — so it stays quiet regardless of the app's log level.
_NOISY_LOGGERS = {
    "aiosqlite": logging.WARNING,
    "httpcore": logging.WARNING,
    "httpx": logging.WARNING,
    "apscheduler": logging.INFO,
}


def _quiet_noisy_loggers() -> None:
    """Pin chatty third-party loggers so they ignore the root level."""
    for name, level in _NOISY_LOGGERS.items():
        logging.getLogger(name).setLevel(level)


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure root logging once at app startup. Idempotent for basicConfig."""
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        _quiet_noisy_loggers()
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
    )
    _quiet_noisy_loggers()
