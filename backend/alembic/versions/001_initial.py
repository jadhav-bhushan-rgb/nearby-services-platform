"""Initial admins and services tables with a PostGIS geography index."""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admins_email", "admins", ["email"], unique=True)
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "category IN ('hospital', 'atm', 'shop', 'other')",
            name="ck_services_category",
        ),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 0 AND rating <= 5)",
            name="ck_services_rating",
        ),
    )
    op.create_index("ix_services_category", "services", ["category"])
    op.create_index("ix_services_created_at", "services", ["created_at"])
    op.execute("CREATE INDEX ix_services_location ON services USING GIST (location)")


def downgrade() -> None:
    op.drop_index("ix_services_location", table_name="services")
    op.drop_index("ix_services_created_at", table_name="services")
    op.drop_index("ix_services_category", table_name="services")
    op.drop_table("services")
    op.drop_index("ix_admins_email", table_name="admins")
    op.drop_table("admins")
