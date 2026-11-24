import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Float, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "category IN ('hospital', 'atm', 'shop', 'other')",
            name="ck_services_category",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 0 AND rating <= 5)",
            name="ck_services_rating",
        ),
        Index("ix_services_category", "category"),
        Index("ix_services_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    service_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
