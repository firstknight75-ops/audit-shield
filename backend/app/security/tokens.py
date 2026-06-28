from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings

settings = get_settings()
ALGORITHM = 'HS256'


def create_token(subject: str, token_type: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': subject,
        'type': token_type,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
