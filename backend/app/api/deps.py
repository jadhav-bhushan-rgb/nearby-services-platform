import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.cache.rate_limit import RateLimiter, remember_limit
from app.cache.redis_client import store
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.services.auth_service import AuthService

bearer = HTTPBearer(auto_error=False)
limiter = RateLimiter(store)


def client_ip(request: Request) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def limit_public(request: Request) -> None:
    snapshot = limiter.enforce(
        f"public:{client_ip(request)}",
        settings.RATE_LIMIT_PUBLIC_PER_MIN,
        60,
        fail_closed=False,
    )
    remember_limit(request, snapshot)


def limit_search(request: Request) -> None:
    snapshot = limiter.enforce(
        f"search:{client_ip(request)}",
        settings.RATE_LIMIT_SEARCH_PER_MIN,
        60,
        fail_closed=False,
    )
    remember_limit(request, snapshot)


def limit_login(request: Request, email: str) -> None:
    ip_snapshot = limiter.enforce(
        f"login:ip:{client_ip(request)}",
        settings.RATE_LIMIT_LOGIN_PER_MIN,
        60,
        fail_closed=True,
    )
    email_snapshot = limiter.enforce(
        f"login:email:{email.lower()}",
        settings.RATE_LIMIT_LOGIN_PER_MIN,
        60,
        fail_closed=True,
    )
    remember_limit(request, ip_snapshot)
    remember_limit(request, email_snapshot)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "NOT_AUTHENTICATED", "Admin authentication is required")
    return AuthService(session).current_admin(credentials.credentials)


def parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise AppError(422, "INVALID_ID", "Service id must be a UUID") from exc
