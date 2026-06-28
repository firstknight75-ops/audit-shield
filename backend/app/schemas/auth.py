from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    preferred_language: str
    permissions: list[str]
    accessible_companies: list[dict]
    last_activity_at: datetime | None = None
