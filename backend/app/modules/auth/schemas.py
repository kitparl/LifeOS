from datetime import datetime
from typing import Annotated

from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator

from app.modules.auth.username_rules import validate_username


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=3, max_length=30)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        try:
            return validate_username(v)
        except ValueError as e:
            raise ValueError(str(e)) from e


class LoginRequest(BaseModel):
    model_config = {"populate_by_name": True}

    identifier: Annotated[
        str,
        Field(min_length=1, max_length=255, validation_alias=AliasChoices("identifier", "email")),
    ]
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    display_name: str
    timezone: str

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class PublicUserResponse(BaseModel):
    username: str
    display_name: str

    model_config = {"from_attributes": True}


class UsernameChangeRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        try:
            return validate_username(v)
        except ValueError as e:
            raise ValueError(str(e)) from e


class UsernameAvailabilityResponse(BaseModel):
    username: str
    available: bool
    reason: str | None = None


class UsernameHistoryEntry(BaseModel):
    id: str
    old_username: str
    new_username: str
    changed_at: datetime
    changed_by: str
    reason: str | None = None

    model_config = {"from_attributes": True}
