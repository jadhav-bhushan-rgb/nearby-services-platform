from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import limit_public, limit_search, parse_uuid
from app.db.session import get_db
from app.schemas.service import (
    MapResponse,
    NearbyResponse,
    ServiceCategory,
    ServiceOut,
    ServicePage,
)
from app.services.service_catalog import ServiceCatalog

router = APIRouter(prefix="/services", tags=["services"])

CATEGORY_LABELS = {
    ServiceCategory.hospital: "Hospitals",
    ServiceCategory.atm: "ATMs",
    ServiceCategory.shop: "Shops",
    ServiceCategory.other: "Others",
}


@router.get("/categories")
def categories(_: None = Depends(limit_public)):
    return [{"id": item.value, "label": CATEGORY_LABELS[item]} for item in ServiceCategory]


@router.get("", response_model=ServicePage)
def list_services(
    request: Request,
    category: ServiceCategory | None = None,
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
    _: None = Depends(limit_public),
):
    query = q.strip() if q else None
    return ServiceCatalog(session).list_services(
        request,
        category=category.value if category else None,
        query=query or None,
        page=page,
        page_size=page_size,
    )


@router.get("/nearby", response_model=NearbyResponse)
def nearby(
    request: Request,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(..., gt=0, le=50),
    category: ServiceCategory | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db),
    _: None = Depends(limit_search),
):
    return ServiceCatalog(session).nearby(
        request,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category=category.value if category else None,
        limit=limit,
    )


@router.get("/map", response_model=MapResponse)
def map_services(
    request: Request,
    min_lat: float = Query(..., ge=-90, le=90),
    min_lng: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    max_lng: float = Query(..., ge=-180, le=180),
    category: ServiceCategory | None = None,
    limit: int = Query(default=300, ge=1, le=500),
    session: Session = Depends(get_db),
    _: None = Depends(limit_search),
):
    return ServiceCatalog(session).map_services(
        request,
        min_lat=min_lat,
        min_lng=min_lng,
        max_lat=max_lat,
        max_lng=max_lng,
        category=category.value if category else None,
        limit=limit,
    )


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(
    service_id: str,
    request: Request,
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    session: Session = Depends(get_db),
    _: None = Depends(limit_public),
):
    if (latitude is None) ^ (longitude is None):
        from app.core.exceptions import AppError

        raise AppError(422, "INVALID_ORIGIN", "Latitude and longitude must be provided together")
    return ServiceCatalog(session).get_service(request, parse_uuid(service_id), latitude, longitude)
