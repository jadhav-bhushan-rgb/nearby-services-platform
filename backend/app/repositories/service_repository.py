import uuid
from dataclasses import dataclass
from datetime import datetime

from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


@dataclass
class ServiceRecord:
    id: uuid.UUID
    name: str
    category: str
    latitude: float
    longitude: float
    rating: float | None
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
    distance_m: float | None = None


class ServiceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: ServiceCreate) -> Service:
        service = Service(
            name=data.name,
            category=data.category.value,
            location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326),
            rating=data.rating,
            service_metadata=data.metadata,
        )
        self.session.add(service)
        self.session.flush()
        self.session.refresh(service)
        return service

    def get(self, service_id: uuid.UUID) -> Service | None:
        return self.session.get(Service, service_id)

    def update(self, service: Service, data: ServiceUpdate) -> Service:
        if data.name is not None:
            service.name = data.name
        if data.category is not None:
            service.category = data.category.value
        if data.latitude is not None and data.longitude is not None:
            service.location = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
        if data.clear_rating:
            service.rating = None
        elif data.rating is not None:
            service.rating = data.rating
        if data.metadata is not None:
            service.service_metadata = data.metadata
        service.updated_at = datetime_now()
        self.session.flush()
        self.session.refresh(service)
        return service

    def delete(self, service: Service) -> None:
        self.session.delete(service)
        self.session.flush()

    def list_page(
        self,
        *,
        category: str | None,
        query: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Service], int]:
        filters = []
        if category:
            filters.append(Service.category == category)
        if query:
            filters.append(Service.name.ilike(like_pattern(query), escape="\\"))
        count_stmt = select(func.count()).select_from(Service)
        list_stmt = select(Service).order_by(Service.created_at.desc())
        if filters:
            count_stmt = count_stmt.where(*filters)
            list_stmt = list_stmt.where(*filters)
        total = self.session.scalar(count_stmt) or 0
        rows = self.session.scalars(
            list_stmt.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return list(rows), int(total)

    def nearby(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        category: str | None,
        limit: int,
    ) -> list[ServiceRecord]:
        statement = text(
            """
            SELECT
                id, name, category, rating, metadata, created_at, updated_at,
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude,
                ST_Distance(
                    location,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) AS distance_m
            FROM services
            WHERE ST_DWithin(
                location,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                :radius_m
            )
            AND (:category IS NULL OR category = :category)
            ORDER BY distance_m ASC
            LIMIT :limit
            """
        )
        rows = self.session.execute(
            statement,
            {
                "lat": latitude,
                "lng": longitude,
                "radius_m": radius_m,
                "category": category,
                "limit": limit,
            },
        ).mappings()
        return [record_from_mapping(row) for row in rows]

    def in_bbox(
        self,
        *,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        category: str | None,
        limit: int,
    ) -> tuple[list[ServiceRecord], bool]:
        statement = text(
            """
            SELECT
                id, name, category, rating, metadata, created_at, updated_at,
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude
            FROM services
            WHERE ST_Intersects(
                location,
                ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)::geography
            )
            AND (:category IS NULL OR category = :category)
            ORDER BY created_at DESC
            LIMIT :limit_plus
            """
        )
        rows = list(
            self.session.execute(
                statement,
                {
                    "min_lat": min_lat,
                    "min_lng": min_lng,
                    "max_lat": max_lat,
                    "max_lng": max_lng,
                    "category": category,
                    "limit_plus": limit + 1,
                },
            ).mappings()
        )
        truncated = len(rows) > limit
        return [record_from_mapping(row) for row in rows[:limit]], truncated

    def distance_to(self, service_id: uuid.UUID, latitude: float, longitude: float) -> float | None:
        statement = text(
            """
            SELECT ST_Distance(
                location,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_m
            FROM services
            WHERE id = :service_id
            """
        )
        return self.session.execute(
            statement,
            {"lat": latitude, "lng": longitude, "service_id": service_id},
        ).scalar()

    def category_counts(self) -> list[tuple[str, int]]:
        rows = self.session.execute(
            select(Service.category, func.count()).group_by(Service.category).order_by(Service.category)
        ).all()
        return [(category, int(count)) for category, count in rows]

    def count(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(Service)) or 0)


def datetime_now() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc)


def like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _extract_coordinates(location) -> tuple[float, float]:
    try:
        point = to_shape(location)
        return float(point.y), float(point.x)
    except Exception:
        pass

    text_val = str(getattr(location, "data", location) or "")
    if "POINT" in text_val.upper():
        import re
        m = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", text_val, re.IGNORECASE)
        if m:
            return float(m.group(2)), float(m.group(1))

    import binascii, struct
    raw = getattr(location, "data", location)
    if isinstance(raw, str):
        try:
            data = binascii.unhexlify(raw)
        except Exception:
            data = raw.encode()
    elif isinstance(raw, (bytes, bytearray, memoryview)):
        data = bytes(raw)
    else:
        data = bytes(str(raw), "utf-8")

    endian = "<" if data[0] == 1 else ">"
    geom_type = struct.unpack(f"{endian}I", data[1:5])[0]
    offset = 9 if (geom_type & 0x20000000) else 5
    lng, lat = struct.unpack(f"{endian}dd", data[offset : offset + 16])
    return float(lat), float(lng)


def to_record(service: Service, distance_m: float | None = None) -> ServiceRecord:
    lat, lng = _extract_coordinates(service.location)
    return ServiceRecord(
        id=service.id,
        name=service.name,
        category=service.category,
        latitude=lat,
        longitude=lng,
        rating=service.rating,
        metadata=service.service_metadata,
        created_at=service.created_at,
        updated_at=service.updated_at,
        distance_m=distance_m,
    )


def record_from_mapping(row) -> ServiceRecord:
    values = dict(row)
    distance = values.get("distance_m")
    return ServiceRecord(
        id=values["id"],
        name=values["name"],
        category=values["category"],
        latitude=float(values["latitude"]),
        longitude=float(values["longitude"]),
        rating=values["rating"],
        metadata=values["metadata"],
        created_at=values["created_at"],
        updated_at=values["updated_at"],
        distance_m=float(distance) if distance is not None else None,
    )

