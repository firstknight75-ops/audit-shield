from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    branch_id: str | None = None


class PermissionOverrideRequest(BaseModel):
    user_id: str
    permission_code: str
    action: str
    reason: str
    expires_at: datetime | None = None
