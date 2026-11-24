import json
import uuid

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete, text

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.admin import Admin
from app.models.service import Service


def _services_available() -> bool:
    if settings.ENV == "production":
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        from app.cache.redis_client import store

        store.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def client():
    if not _services_available():
        pytest.skip("PostGIS and Redis must be running for integration tests")
    command.upgrade(Config("alembic.ini"), "head")
    with engine.connect() as connection:
        version = connection.execute(text("SELECT PostGIS_Version()")).scalar()
    assert version
    _ensure_admin()
    with TestClient(app) as test_client:
        yield test_client
    _delete_test_services()


def _ensure_admin():
    from sqlalchemy import select

    email = settings.ADMIN_EMAIL.lower()
    with SessionLocal() as session:
        existing = session.scalar(select(Admin).where(Admin.email == email))
        if existing is None:
            session.add(
                Admin(
                    email=email,
                    hashed_password=hash_password(settings.ADMIN_PASSWORD),
                    full_name="Test Admin",
                    is_active=True,
                )
            )
        else:
            existing.hashed_password = hash_password(settings.ADMIN_PASSWORD)
            existing.is_active = True
        session.commit()


def _delete_test_services():
    with SessionLocal() as session:
        session.execute(delete(Service).where(Service.name.like("IT %")))
        session.commit()


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _create(client: TestClient, token: str, **payload):
    response = client.post(
        "/api/v1/admin/services",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_public_routes_require_no_login_and_admin_routes_do(client: TestClient):
    listing = client.get("/api/v1/services", params={"page_size": 1})
    assert listing.status_code == 200
    assert listing.headers["X-Cache"] in {"HIT", "MISS", "BYPASS"}
    blocked = client.post(
        "/api/v1/admin/services",
        json={"name": "Nope", "category": "shop", "latitude": 12.97, "longitude": 77.59},
    )
    assert blocked.status_code == 401


def test_nearby_search_orders_by_distance_and_uses_cache(client: TestClient):
    token = _login(client)
    suffix = uuid.uuid4().hex[:8]
    close = _create(
        client,
        token,
        name=f"IT Close {suffix}",
        category="hospital",
        latitude=12.972,
        longitude=77.595,
        rating=4.5,
        metadata={"address": "MG Road"},
    )
    far = _create(
        client,
        token,
        name=f"IT Far {suffix}",
        category="atm",
        latitude=12.9352,
        longitude=77.6245,
    )
    params = {"latitude": 12.9716, "longitude": 77.5946, "radius_km": 8, "limit": 50}
    first = client.get("/api/v1/services/nearby", params=params)
    second = client.get("/api/v1/services/nearby", params=params)
    assert first.status_code == 200
    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    window = client.get(
        "/api/v1/services/map",
        params={"min_lat": 12.96, "min_lng": 77.58, "max_lat": 12.99, "max_lng": 77.62, "limit": 200},
    )
    assert window.status_code == 200, window.text
    assert any(item["id"] == close["id"] for item in window.json()["items"])

    names = [item["name"] for item in first.json()["items"]]
    assert names.index(close["name"]) < names.index(far["name"])
    distances = [item["distance_km"] for item in first.json()["items"]]
    assert distances == sorted(distances)

    tight = client.get(
        "/api/v1/services/nearby",
        params={"latitude": 12.9716, "longitude": 77.5946, "radius_km": 0.4, "category": "hospital"},
    )
    tight_names = [item["name"] for item in tight.json()["items"]]
    assert close["name"] in tight_names
    assert far["name"] not in tight_names

    renamed = client.put(
        f"/api/v1/admin/services/{close['id']}",
        json={"name": f"IT Renamed {suffix}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert renamed.status_code == 200
    refreshed = client.get("/api/v1/services/nearby", params=params)
    assert refreshed.headers["X-Cache"] == "MISS"
    assert any(item["name"] == f"IT Renamed {suffix}" for item in refreshed.json()["items"])

    detail = client.get(
        f"/api/v1/services/{close['id']}",
        params={"latitude": 12.9716, "longitude": 77.5946},
    )
    assert detail.status_code == 200
    assert detail.json()["distance_km"] is not None
    assert detail.json()["distance_km"] < 1

    removed = client.delete(
        f"/api/v1/admin/services/{far['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert removed.status_code == 204
    missing = client.get(f"/api/v1/services/{far['id']}")
    assert missing.status_code == 404


def test_login_and_refresh_rotation(client: TestClient):
    denied = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@nearby.local", "password": "ChangeMe123!"},
    )
    assert denied.status_code == 401
    assert denied.json()["error"]["code"] == "INVALID_CREDENTIALS"

    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    body = logged_in.json()
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert rotated.status_code == 200
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert reused.status_code == 401


def test_bulk_json_upload(client: TestClient):
    token = _login(client)
    payload = json.dumps(
        [{"name": "IT Bulk Shop", "category": "shop", "latitude": 12.97, "longitude": 77.6, "rating": 3}]
    )
    response = client.post(
        "/api/v1/admin/services/bulk",
        files={"file": ("services.json", payload, "application/json")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["created"] == 1
