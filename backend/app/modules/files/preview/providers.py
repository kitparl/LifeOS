from __future__ import annotations

from typing import Protocol

from app.modules.files.preview_schemas import PreviewType

# Bumped whenever the LibreOffice conversion pipeline changes in a way that
# should invalidate previously cached PDFs (e.g. different soffice flags).
CONVERTER_VERSION = "1"

IMAGE_MIME_TYPES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "image/svg+xml",
        "image/bmp",
    }
)

# TIFF is intentionally not converted to PNG (would need Pillow, a new
# dependency, for one rare format) — it reports as unsupported/download-only.
TEXT_MIME_TYPES = frozenset(
    {
        "text/plain",
        "application/json",
        "text/xml",
    }
)
CSV_MIME_TYPES = frozenset({"text/csv"})
MARKDOWN_MIME_TYPES = frozenset({"text/markdown"})

VIDEO_MIME_TYPES = frozenset({"video/mp4", "video/webm"})
AUDIO_MIME_TYPES = frozenset({"audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/ogg", "audio/x-wav"})

OFFICE_MIME_TYPES = frozenset(
    {
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.oasis.opendocument.text",
        "application/rtf",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.spreadsheet",
    }
)


class PreviewProvider(Protocol):
    """Extension point: one provider per rendering strategy.

    Deliberately minimal — no plugin discovery/factories/metaclasses, just an
    ordered list checked in order (see PROVIDERS below).
    """

    def can_handle(self, content_type: str) -> bool: ...

    def preview_type(self, content_type: str) -> PreviewType: ...

    def needs_conversion(self) -> bool: ...


class _StaticProvider:
    def __init__(self, mime_types: frozenset[str], preview_type_value: PreviewType, *, converts: bool = False):
        self._mime_types = mime_types
        self._preview_type_value = preview_type_value
        self._converts = converts

    def can_handle(self, content_type: str) -> bool:
        return content_type in self._mime_types

    def preview_type(self, content_type: str) -> PreviewType:
        return self._preview_type_value

    def needs_conversion(self) -> bool:
        return self._converts


PdfProvider = _StaticProvider(frozenset({"application/pdf"}), "pdf")
ImageProvider = _StaticProvider(IMAGE_MIME_TYPES, "image")
CsvProvider = _StaticProvider(CSV_MIME_TYPES, "csv")
MarkdownProvider = _StaticProvider(MARKDOWN_MIME_TYPES, "markdown")
TextProvider = _StaticProvider(TEXT_MIME_TYPES, "text")
VideoProvider = _StaticProvider(VIDEO_MIME_TYPES, "video")
AudioProvider = _StaticProvider(AUDIO_MIME_TYPES, "audio")
OfficeProvider = _StaticProvider(OFFICE_MIME_TYPES, "pdf", converts=True)

# Order matters only in that the first match wins; sets don't overlap today.
PROVIDERS: list[PreviewProvider] = [
    PdfProvider,
    ImageProvider,
    CsvProvider,
    MarkdownProvider,
    TextProvider,
    VideoProvider,
    AudioProvider,
    OfficeProvider,
]


def find_provider(content_type: str) -> PreviewProvider | None:
    for provider in PROVIDERS:
        if provider.can_handle(content_type):
            return provider
    return None


def detect_preview_type(content_type: str) -> PreviewType:
    provider = find_provider(content_type)
    return provider.preview_type(content_type) if provider else "unsupported"
