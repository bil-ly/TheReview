from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.review import EntityType, Platform


# Base schema with common fields
class ReviewBase(BaseModel):
    """Base schema for Review with common fields."""

    entity_type: EntityType
    entity_name: str = Field(..., min_length=1, max_length=500)
    entity_identifier: str | None = Field(None, max_length=255)
    platform: Platform
    platform_review_id: str = Field(..., min_length=1, max_length=255)
    reviewer_name: str | None = Field(None, max_length=255)
    reviewer_identifier: str | None = Field(None, max_length=255)
    reviewer_profile_url: HttpUrl | str | None = None
    rating: float | None = Field(None, ge=0.0, le=5.0)
    review_title: str | None = Field(None, max_length=500)
    review_text: str = Field(..., min_length=1)
    review_url: HttpUrl | str | None = None
    review_date: datetime
    helpful_count: int = Field(default=0, ge=0)
    verified: bool = Field(default=False)
    sentiment_score: float | None = Field(None, ge=-1.0, le=1.0)
    response_text: str | None = None
    response_date: datetime | None = None
    images: list[str] | None = None
    extra_data: dict | None = None  # Platform-specific metadata


# Schema for creating a new review
class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""

    pass


# Schema for updating an existing review
class ReviewUpdate(BaseModel):
    """Schema for updating a review (all fields optional)."""

    entity_type: EntityType | None = None
    entity_name: str | None = Field(None, min_length=1, max_length=500)
    entity_identifier: str | None = Field(None, max_length=255)
    platform: Platform | None = None
    platform_review_id: str | None = Field(None, min_length=1, max_length=255)
    reviewer_name: str | None = Field(None, max_length=255)
    reviewer_identifier: str | None = Field(None, max_length=255)
    reviewer_profile_url: HttpUrl | str | None = None
    rating: float | None = Field(None, ge=0.0, le=5.0)
    review_title: str | None = Field(None, max_length=500)
    review_text: str | None = Field(None, min_length=1)
    review_url: HttpUrl | str | None = None
    review_date: datetime | None = None
    helpful_count: int | None = Field(None, ge=0)
    verified: bool | None = None
    sentiment_score: float | None = Field(None, ge=-1.0, le=1.0)
    response_text: str | None = None
    response_date: datetime | None = None
    images: list[str] | None = None
    extra_data: dict | None = None  # Platform-specific metadata
    is_active: bool | None = None


# Schema for reading a review (response)
class ReviewResponse(ReviewBase):
    """Schema for review response."""

    id: UUID
    scraped_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schema for paginated list of reviews
class ReviewListResponse(BaseModel):
    """Schema for paginated review list response."""

    total: int
    page: int
    page_size: int
    total_pages: int
    reviews: list[ReviewResponse]


# Schema for review statistics/aggregations
class ReviewStats(BaseModel):
    """Schema for review statistics."""

    total_reviews: int
    average_rating: float | None
    rating_distribution: dict[str, int]  # e.g., {"5": 100, "4": 50, ...}
    platform_distribution: dict[str, int]  # e.g., {"google": 150, "yelp": 75}
    entity_type_distribution: dict[str, int]
    verified_count: int
    with_response_count: int
    sentiment_distribution: dict[str, int] | None  # e.g., {"positive": 100, ...}


# Schema for bulk operations
class BulkReviewCreate(BaseModel):
    """Schema for creating multiple reviews at once."""

    reviews: list[ReviewCreate] = Field(..., min_length=1, max_length=1000)


class BulkReviewResponse(BaseModel):
    """Schema for bulk operation response."""

    success_count: int
    failed_count: int
    errors: list[dict[str, str]] = []
    created_ids: list[UUID] = []


# Schema for filtering reviews
class ReviewFilter(BaseModel):
    """Schema for filtering reviews in queries."""

    entity_type: EntityType | None = None
    entity_name: str | None = None
    entity_identifier: str | None = None
    platform: Platform | None = None
    min_rating: float | None = Field(None, ge=0.0, le=5.0)
    max_rating: float | None = Field(None, ge=0.0, le=5.0)
    verified_only: bool = False
    with_response_only: bool = False
    is_active: bool = True
    start_date: datetime | None = None
    end_date: datetime | None = None
    search_text: str | None = None  # Full-text search in review_text
