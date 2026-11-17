from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

PlannerNodeKind = Literal["project", "folder", "diagram"]

NAME_MAX_LENGTH = 200


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return None
    name = value.strip()
    if not name or len(name) > NAME_MAX_LENGTH:
        raise ValueError(f"Name must be 1-{NAME_MAX_LENGTH} characters")
    if "/" in name or "\\" in name:
        raise ValueError("Name must not contain '/' or '\\'")
    return name


class _NamedNode(BaseModel):
    @field_validator("name", check_fields=False)
    @classmethod
    def _validate_name(cls, v: str | None) -> str | None:
        return _clean_name(v)


class PlannerNodeCreate(_NamedNode):
    parent_id: str | None = None
    kind: PlannerNodeKind
    name: str


class PlannerNodeUpdate(_NamedNode):
    """A move is signalled by `parent_id` being present in the payload (even as null)."""

    name: str | None = None
    parent_id: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class PlannerNodeResponse(BaseModel):
    id: str
    parent_id: str | None
    kind: str
    name: str
    order_index: int
    revision: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlannerContentResponse(BaseModel):
    content: str
    revision: int


class PlannerContentUpdate(BaseModel):
    content: str
    base_revision: int = Field(ge=1)
