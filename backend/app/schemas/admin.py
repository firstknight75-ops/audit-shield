from datetime import datetime

from pydantic import BaseModel, EmailStr


class CompanyAccessGrant(BaseModel):
    company_id: str
    branch_id: str | None = None


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    preferred_language: str | None = None
    company_access: list[CompanyAccessGrant] = []


class PermissionOverrideRequest(BaseModel):
    user_id: str
    permission_code: str
    action: str
    reason: str
    company_id: str | None = None
    expires_at: datetime | None = None


class UpdateLanguageRequest(BaseModel):
    preferred_language: str
