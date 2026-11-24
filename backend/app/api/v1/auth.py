from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import bearer, limit_login
from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.auth import AdminOut, LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.services.auth_service import AuthService, admin_out

router = APIRouter(prefix="/auth", tags=["auth"])


def _bearer_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "NOT_AUTHENTICATED", "Admin authentication is required")
    return credentials.credentials


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, session: Session = Depends(get_db)):
    limit_login(request, body.email)
    return AuthService(session).login(str(body.email), body.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, session: Session = Depends(get_db)):
    return AuthService(session).refresh(body.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    body: LogoutRequest,
    token: str = Depends(_bearer_token),
    session: Session = Depends(get_db),
):
    service = AuthService(session)
    service.current_admin(token)
    service.logout(token, body.refresh_token)


@router.get("/me", response_model=AdminOut)
def me(token: str = Depends(_bearer_token), session: Session = Depends(get_db)):
    return admin_out(AuthService(session).current_admin(token))
