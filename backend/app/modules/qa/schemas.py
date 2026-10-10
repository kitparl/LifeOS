from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.text import is_http_url

QA_LINKS_MAX = 20
QA_LINK_MAX_LENGTH = 2048


def _clean_links(links: list[str] | None) -> list[str] | None:
    """Trim, drop blanks and duplicates, and require http(s) URLs."""
    if links is None:
        return None
    cleaned: list[str] = []
    for raw in links:
        link = raw.strip()
        if not link or link in cleaned:
            continue
        if len(link) > QA_LINK_MAX_LENGTH or not is_http_url(link):
            raise ValueError(f"Invalid link: {link[:80]} (must start with http:// or https://)")
        cleaned.append(link)
    if len(cleaned) > QA_LINKS_MAX:
        raise ValueError(f"At most {QA_LINKS_MAX} links allowed")
    return cleaned


class QACreate(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    type: str | None = Field(default=None, max_length=64)
    tags: list[str] = []
    links: list[str] = []
    is_deep_personal: bool = False
    linked_journal_id: str | None = None

    _validate_links = field_validator("links")(_clean_links)


class QAUpdate(BaseModel):
    question: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)
    type: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = None
    links: list[str] | None = None
    is_deep_personal: bool | None = None
    linked_journal_id: str | None = None

    _validate_links = field_validator("links")(_clean_links)


class QATypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class QAVersionResponse(BaseModel):
    id: str
    version_number: int
    answer: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QAListItem(BaseModel):
    id: str
    question: str
    current_answer: str | None = None
    type: str | None = None
    tags: list[str]
    links: list[str] = []
    is_deep_personal: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class QAResponse(BaseModel):
    id: str
    question: str
    current_answer: str
    type: str | None = None
    tags: list[str]
    links: list[str] = []
    is_deep_personal: bool = False
    linked_journal_id: str | None
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime
    versions: list[QAVersionResponse] = []
