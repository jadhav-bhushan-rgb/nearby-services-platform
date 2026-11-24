from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, limit_public, parse_uuid
from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.service import (
    BulkImportResponse,
    ServiceCategory,
    ServiceCreate,
    ServiceOut,
    ServicePage,
    ServiceUpdate,
    StatsResponse,
)
from app.services.bulk_import import parse_upload
from app.services.service_catalog import ServiceCatalog

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=StatsResponse)
def stats(
    request: Request,
    session: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    __: None = Depends(limit_public),
):
    return ServiceCatalog(session).stats(request)


@router.get("/services", response_model=ServicePage)
def list_services(
    request: Request,
    category: ServiceCategory | None = None,
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    __: None = Depends(limit_public),
):
    query = q.strip() if q else None
    return ServiceCatalog(session).list_services(
        request,
        category=category.value if category else None,
        query=query or None,
        page=page,
        page_size=page_size,
    )


@router.post("/services", response_model=ServiceOut, status_code=201)
def create_service(
    body: ServiceCreate,
    session: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    __: None = Depends(limit_public),
):
    return ServiceCatalog(session).create(body)


@router.post("/services/bulk", response_model=BulkImportResponse)
def bulk_upload(
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    __: None = Depends(limit_public),
):
    payload = file.file.read()
    try:
        rows, errors = parse_upload(file.filename or "", payload)
    except ValueError as exc:
        raise AppError(422, "INVALID_UPLOAD", str(exc)) from exc
    return ServiceCatalog(session).bulk_create(rows, errors)


@router.put("/services/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: str,
    body: ServiceUpdate,
    session: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    __: None = Depends(limit_public),
):
    return ServiceCatalog(session).update(parse_uuid(service_id), body)


@router.delete("/services/{service_id}", status_code=204)
def delete_service(
    service_id: str,
    session: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    __: None = Depends(limit_public),
):
    ServiceCatalog(session).delete(parse_uuid(service_id))
