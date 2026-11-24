import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import AppError

_dummy_hash: str | None = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def dummy_password_hash() -> str:
    """Hash used when the email does not exist so login timing stays similar."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("not-a-real-password")
    return _dummy_hash


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, int]:
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    exp = now + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    encoded = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded, jti, int(expires_delta.total_seconds())


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AppError(401, "INVALID_TOKEN", "Invalid or expired token") from exc
    if payload.get("type") != expected_type or not payload.get("sub") or not payload.get("jti"):
        raise AppError(401, "INVALID_TOKEN", "Invalid or expired token")
    return payload
