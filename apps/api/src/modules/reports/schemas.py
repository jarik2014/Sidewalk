import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.enums import ReportCategory, ReportStatus
from src.modules.reports.media import validate_media_urls


class CreateReportRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=1)
    category: ReportCategory
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    address: str | None = Field(default=None, max_length=500)
    media_urls: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("media_urls")
    @classmethod
    def _validate_media_urls(cls, urls: list[str]) -> list[str]:
        return validate_media_urls(urls) or []

    @model_validator(mode="after")
    def validate_location(self) -> "CreateReportRequest":
        if (self.latitude is not None and self.longitude is None) or (
            self.latitude is None and self.longitude is not None
        ):
            raise ValueError("Both latitude and longitude must be provided together, or neither")
        return self


class UpdateReportRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    category: ReportCategory | None = None
    status: ReportStatus | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    address: str | None = Field(default=None, max_length=500)
    media_urls: list[str] | None = Field(default=None, max_length=10)

    @field_validator("media_urls")
    @classmethod
    def _validate_media_urls(cls, urls: list[str] | None) -> list[str] | None:
        return validate_media_urls(urls)

    @model_validator(mode="after")
    def validate_location(self) -> "UpdateReportRequest":
        if (self.latitude is not None and self.longitude is None) or (
            self.latitude is None and self.longitude is not None
        ):
            raise ValueError("Both latitude and longitude must be provided together, or neither")
        return self


class ReportResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category: ReportCategory
    status: ReportStatus
    user_id: uuid.UUID
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    is_deleted: bool = False
    flagged: bool = False
    flag_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
