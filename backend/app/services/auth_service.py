import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from app.cache.redis_client import store
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import (
    create_token,
    decode_token,
    dummy_password_hash,
    hash_password,
    verify_password,
)
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.schemas.auth import AdminOut, TokenResponse


class AuthService:
    def __init__(self, session: Session) -> None:
        self.admins = AdminRepository(session)

    def login(self, email: str, password: str) -> TokenResponse:
        admin = self.admins.get_by_email(email.lower())
        if admin is None or not admin.is_active:
            verify_password(password, dummy_password_hash())
            raise AppError(401, "INVALID_CREDENTIALS", "Invalid email or password")
        if not verify_password(password, admin.hashed_password):
            raise AppError(401, "INVALID_CREDENTIALS", "Invalid email or password")
        return self._issue_tokens(admin)

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, "refresh")
        jti = payload["jti"]
        admin_id = self._take_refresh_jti(jti)
        if admin_id is None or admin_id != payload["sub"]:
            raise AppError(401, "INVALID_TOKEN", "Refresh token is no longer valid")
        admin = self.admins.get_by_id(uuid.UUID(admin_id))
        if admin is None or not admin.is_active:
            raise AppError(401, "INVALID_TOKEN", "Refresh token is no longer valid")
        return self._issue_tokens(admin)

    def logout(self, access_token: str, refresh_token: str) -> None:
        access = decode_token(access_token, "access")
        self._blacklist(access["jti"], int(access["exp"]))
        refresh = decode_token(refresh_token, "refresh")
        store.delete(self._refresh_key(refresh["jti"]))

    def current_admin(self, token: str) -> Admin:
        payload = decode_token(token, "access")
        self._assert_not_revoked(payload["jti"])
        admin = self.admins.get_by_id(uuid.UUID(payload["sub"]))
        if admin is None or not admin.is_active:
            raise AppError(401, "INVALID_TOKEN", "Invalid or expired token")
        return admin

    def _issue_tokens(self, admin: Admin) -> TokenResponse:
        access, _, access_ttl = create_token(
            str(admin.id),
            "access",
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh, refresh_jti, refresh_ttl = create_token(
            str(admin.id),
            "refresh",
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        try:
            store.set(self._refresh_key(refresh_jti), str(admin.id), ex=refresh_ttl)
        except Exception as exc:
            raise AppError(503, "AUTH_UNAVAILABLE", "Authentication store unavailable") from exc
        return TokenResponse(access_token=access, refresh_token=refresh, expires_in=access_ttl)

    def _take_refresh_jti(self, jti: str) -> str | None:
        key = self._refresh_key(jti)
        try:
            admin_id = store.get(key)
            if admin_id is not None:
                store.delete(key)
            return admin_id
        except Exception as exc:
            raise AppError(503, "AUTH_UNAVAILABLE", "Authentication store unavailable") from exc

    def _assert_not_revoked(self, jti: str) -> None:
        try:
            if store.get(self._blacklist_key(jti)):
                raise AppError(401, "TOKEN_REVOKED", "Token has been revoked")
        except AppError:
            raise
        except Exception as exc:
            raise AppError(503, "AUTH_UNAVAILABLE", "Authentication store unavailable") from exc

    def _blacklist(self, jti: str, exp: int) -> None:
        from datetime import datetime, timezone

        ttl = max(exp - int(datetime.now(timezone.utc).timestamp()), 1)
        try:
            store.set(self._blacklist_key(jti), "1", ex=ttl)
        except Exception as exc:
            raise AppError(503, "AUTH_UNAVAILABLE", "Authentication store unavailable") from exc

    @staticmethod
    def _refresh_key(jti: str) -> str:
        return f"auth:refresh:{jti}"

    @staticmethod
    def _blacklist_key(jti: str) -> str:
        return f"auth:blacklist:{jti}"


def admin_out(admin: Admin) -> AdminOut:
    return AdminOut(id=admin.id, email=admin.email, full_name=admin.full_name, is_active=admin.is_active)


def seed_admin_password(password: str) -> str:
    return hash_password(password)
