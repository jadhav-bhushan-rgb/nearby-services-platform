import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ServiceCategory(str, Enum):
    hospital = "hospital"
    atm = "atm"
    shop = "shop"
    other = "other"


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: ServiceCategory
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    rating: float | None = Field(default=None, ge=0, le=5)
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name is required")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def limit_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        if len(json.dumps(value)) > 8000:
            raise ValueError("Metadata exceeds 8000 characters")
        return value


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: ServiceCategory | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    rating: float | None = Field(default=None, ge=0, le=5)
    metadata: dict[str, Any] | None = None
    clear_rating: bool = False

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name is required")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def limit_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        if len(json.dumps(value)) > 8000:
            raise ValueError("Metadata exceeds 8000 characters")
        return value

    @model_validator(mode="after")
    def coordinates_together(self) -> "ServiceUpdate":
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("Latitude and longitude must be updated together")
        return self


class ServiceOut(BaseModel):
    id: UUID
    name: str
    category: ServiceCategory
    latitude: float
    longitude: float
    rating: float | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    distance_km: float | None = None


class ServicePage(BaseModel):
    items: list[ServiceOut]
    total: int
    page: int
    page_size: int


class NearbyResponse(BaseModel):
    items: list[ServiceOut]
    latitude: float
    longitude: float
    radius_km: float
    count: int


class MapResponse(BaseModel):
    items: list[ServiceOut]
    count: int
    truncated: bool


class CategoryCount(BaseModel):
    category: ServiceCategory
    count: int


class StatsResponse(BaseModel):
    total: int
    by_category: list[CategoryCount]


class BulkImportResponse(BaseModel):
    created: int
    failed: int
    errors: list[dict[str, Any]]
