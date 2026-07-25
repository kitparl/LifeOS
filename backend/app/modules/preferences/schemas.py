from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PreferenceValueUpdate(BaseModel):
    value: Any = None


class PreferenceResponse(BaseModel):
    key: str
    value: Any = None
    updated_at: datetime | None = None


class PreferenceListItem(BaseModel):
    key: str
    value: Any = None
    updated_at: datetime | None = None
