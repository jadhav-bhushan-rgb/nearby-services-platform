import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.cache import keys
from app.cache.redis_client import store
from app.core.config import settings
from app.core.exceptions import AppError
from app.repositories.service_repository import ServiceRepository, to_record
from app.schemas.service import (
    BulkImportResponse,
    CategoryCount,
    MapResponse,
    NearbyResponse,
    ServiceCategory,
    ServiceCreate,
    ServiceOut,
    ServicePage,
    ServiceUpdate,
    StatsResponse,
)


class ServiceCatalog:
    def __init__(self, session: Session) -> None:
        self.repo = ServiceRepository(session)

    def create(self, data: ServiceCreate) -> ServiceOut:
        service = self.repo.create(data)
        self._invalidate()
        return to_out(to_record(service))

    def update(self, service_id: uuid.UUID, data: ServiceUpdate) -> ServiceOut:
        service = self._require(service_id)
        updated = self.repo.update(service, data)
        self._invalidate()
        return to_out(to_record(updated))

    def delete(self, service_id: uuid.UUID) -> None:
        service = self._require(service_id)
        self.repo.delete(service)
        self._invalidate()

    def bulk_create(self, rows: list[tuple[int, ServiceCreate]], errors: list[dict]) -> BulkImportResponse:
        created = 0
        for row_number, row in rows:
            try:
                with self.repo.session.begin_nested():
                    self.repo.create(row)
                created += 1
            except Exception:
                errors.append({"row": row_number, "message": f"Could not save '{row.name}'"})
        if created:
            self._invalidate()
        return BulkImportResponse(created=created, failed=len(errors), errors=errors[:50])

    def list_services(
        self,
        request: Request,
        *,
        category: str | None,
        query: str | None,
        page: int,
        page_size: int,
    ) -> ServicePage:
        version = store.version()
        cache_key = None
        if version is not None:
            cache_key = keys.list_key(version, category, query, page, page_size)
            cached = store.get_json(cache_key)
            if cached is not None:
                mark_cache(request, "HIT")
                return ServicePage.model_validate(cached)
        records, total = self.repo.list_page(category=category, query=query, page=page, page_size=page_size)
        page_model = ServicePage(
            items=[to_out(to_record(row)) for row in records],
            total=total,
            page=page,
            page_size=page_size,
        )
        if cache_key:
            store.set_json(cache_key, page_model.model_dump(mode="json"), settings.CACHE_TTL_LIST_SECONDS)
            mark_cache(request, "MISS")
        else:
            mark_cache(request, "BYPASS")
        return page_model

    def get_service(
        self,
        request: Request,
        service_id: uuid.UUID,
        latitude: float | None,
        longitude: float | None,
    ) -> ServiceOut:
        version = store.version()
        cache_key = None
        if version is not None:
            cache_key = keys.detail_key(version, str(service_id), latitude, longitude)
            cached = store.get_json(cache_key)
            if cached is not None:
                mark_cache(request, "HIT")
                return ServiceOut.model_validate(cached)
        service = self._require(service_id)
        distance_m = None
        if latitude is not None and longitude is not None:
            distance_m = self.repo.distance_to(service_id, latitude, longitude)
        result = to_out(to_record(service, distance_m))
        if cache_key:
            store.set_json(cache_key, result.model_dump(mode="json"), settings.CACHE_TTL_DETAIL_SECONDS)
            mark_cache(request, "MISS")
        else:
            mark_cache(request, "BYPASS")
        return result

    def nearby(
        self,
        request: Request,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: str | None,
        limit: int,
    ) -> NearbyResponse:
        version = store.version()
        cache_key = None
        if version is not None:
            cache_key = keys.nearby_key(version, latitude, longitude, radius_km, category, limit)
            cached = store.get_json(cache_key)
            if cached is not None:
                mark_cache(request, "HIT")
                return NearbyResponse.model_validate(cached)
        records = self.repo.nearby(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_km * 1000,
            category=category,
            limit=limit,
        )
        result = NearbyResponse(
            items=[to_out(row) for row in records],
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            count=len(records),
        )
        if cache_key:
            store.set_json(cache_key, result.model_dump(mode="json"), settings.CACHE_TTL_NEARBY_SECONDS)
            mark_cache(request, "MISS")
        else:
            mark_cache(request, "BYPASS")
        return result

    def map_services(
        self,
        request: Request,
        *,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        category: str | None,
        limit: int,
    ) -> MapResponse:
        if min_lat >= max_lat or min_lng >= max_lng:
            raise AppError(422, "INVALID_BOUNDS", "Bounding box minimums must be less than maximums")
        version = store.version()
        cache_key = None
        if version is not None:
            cache_key = keys.map_key(version, min_lat, min_lng, max_lat, max_lng, category, limit)
            cached = store.get_json(cache_key)
            if cached is not None:
                mark_cache(request, "HIT")
                return MapResponse.model_validate(cached)
        records, truncated = self.repo.in_bbox(
            min_lat=min_lat,
            min_lng=min_lng,
            max_lat=max_lat,
            max_lng=max_lng,
            category=category,
            limit=limit,
        )
        result = MapResponse(items=[to_out(row) for row in records], count=len(records), truncated=truncated)
        if cache_key:
            store.set_json(cache_key, result.model_dump(mode="json"), settings.CACHE_TTL_MAP_SECONDS)
            mark_cache(request, "MISS")
        else:
            mark_cache(request, "BYPASS")
        return result

    def stats(self, request: Request) -> StatsResponse:
        version = store.version()
        cache_key = keys.stats_key(version) if version is not None else None
        if cache_key:
            cached = store.get_json(cache_key)
            if cached is not None:
                mark_cache(request, "HIT")
                return StatsResponse.model_validate(cached)
        counts = dict(self.repo.category_counts())
        by_category = [
            CategoryCount(category=ServiceCategory(name), count=counts.get(name, 0))
            for name in ServiceCategory
        ]
        result = StatsResponse(total=sum(item.count for item in by_category), by_category=by_category)
        if cache_key:
            store.set_json(cache_key, result.model_dump(mode="json"), settings.CACHE_TTL_LIST_SECONDS)
            mark_cache(request, "MISS")
        else:
            mark_cache(request, "BYPASS")
        return result

    def _invalidate(self) -> None:
        self.repo.session.info["invalidate_services"] = True

    def _require(self, service_id: uuid.UUID):
        service = self.repo.get(service_id)
        if service is None:
            raise AppError(404, "NOT_FOUND", "Service not found")
        return service


def to_out(record) -> ServiceOut:
    distance_km = None
    if record.distance_m is not None:
        distance_km = round(record.distance_m / 1000, 3)
    return ServiceOut(
        id=record.id,
        name=record.name,
        category=record.category,
        latitude=record.latitude,
        longitude=record.longitude,
        rating=record.rating,
        metadata=record.metadata,
        created_at=record.created_at,
        updated_at=record.updated_at,
        distance_km=distance_km,
    )


def mark_cache(request: Request, status: str) -> None:
    request.state.cache_status = status
