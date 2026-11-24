import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.cache.redis_client import store
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.db.session import engine

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        summary="Discover nearby hospitals, ATMs, shops, and other services.",
        description=(
            "Public map and nearby search need no account. "
            "Admin routes require a JWT from POST /api/v1/auth/login. "
            "Geospatial queries use PostGIS. Redis caches reads and rate limits clients."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(GZipMiddleware, minimum_size=800)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_context)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.add_api_route("/health", health, methods=["GET"], tags=["health"])

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "HTTP_ERROR", "message": message}},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [
                        {"loc": list(error.get("loc", [])), "msg": error.get("msg"), "type": error.get("type")}
                        for error in exc.errors()
                    ],
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Unexpected server error"}},
        )

    return app


async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    rate_limit = getattr(request.state, "rate_limit", None)
    if rate_limit:
        response.headers["X-RateLimit-Limit"] = str(rate_limit["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit["remaining"])
    cache_status = getattr(request.state, "cache_status", None)
    if cache_status:
        response.headers["X-Cache"] = cache_status
    elapsed = (time.perf_counter() - started) * 1000
    logger.info("%s %s -> %s %.1fms", request.method, request.url.path, response.status_code, elapsed)
    return response


def health():
    database = _check_database()
    redis_ok = _check_redis()
    status = "ok" if database and redis_ok else "degraded"
    return JSONResponse(
        status_code=200 if status == "ok" else 503,
        content={"status": status, "database": database, "redis": redis_ok},
    )


def _check_database() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False


def _check_redis() -> bool:
    try:
        return bool(store.ping())
    except Exception:
        logger.exception("Redis health check failed")
        return False


app = create_app()
