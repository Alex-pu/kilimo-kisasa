from pydantic import BaseModel, Field, model_validator
from typing import Optional


class LocalLoginRequest(BaseModel):
    identity: str = Field(..., description="Email address or username")
    password: str

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_fields(cls, data):
        if isinstance(data, dict) and "identity" not in data:
            legacy_identity = data.get("username_or_email") or data.get("email")
            if legacy_identity:
                data = {**data, "identity": legacy_identity}
        return data


class LocalRegisterRequest(BaseModel):
    identity: str = Field(..., description="Email address or username")
    display_name: str
    password: str
    password_verify: str

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_fields(cls, data):
        if isinstance(data, dict):
            updates = {}
            if "identity" not in data:
                legacy_identity = data.get("email") or data.get("username")
                if legacy_identity:
                    updates["identity"] = legacy_identity
            if "display_name" not in data and data.get("username"):
                updates["display_name"] = data["username"]
            if updates:
                data = {**data, **updates}
        return data


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
