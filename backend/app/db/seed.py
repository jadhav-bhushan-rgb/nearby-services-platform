"""Create the default admin and load the sample dataset when the table is empty."""

import json
from pathlib import Path

from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import Admin
from app.models.service import Service
from app.schemas.service import ServiceCreate
from app.services.bulk_import import _normalize

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_services.json"


def seed_admin() -> None:
    email = settings.ADMIN_EMAIL.lower()
    with SessionLocal() as session:
        existing = session.scalar(select(Admin).where(Admin.email == email))
        if existing:
            return
        session.add(
            Admin(
                email=email,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name=settings.ADMIN_NAME,
                is_active=True,
            )
        )
        session.commit()
        print(f"Created admin {email}")


def seed_services() -> int:
    if not settings.SEED_SAMPLE_DATA:
        return 0
    payload = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(Service)) or 0
        if count:
            print(f"Services already present ({count}); skipping sample load")
            return 0
        for raw in payload:
            session.add(_service_from_raw(raw))
        session.commit()
    print(f"Loaded {len(payload)} sample services")
    return len(payload)


def _service_from_raw(raw: dict) -> Service:
    from geoalchemy2.elements import WKTElement

    data: ServiceCreate = _normalize(raw)
    return Service(
        name=data.name,
        category=data.category.value,
        location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326),
        rating=data.rating,
        service_metadata=data.metadata,
    )


def main() -> None:
    seed_admin()
    seed_services()


if __name__ == "__main__":
    main()
