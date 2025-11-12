import enum
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class EntityType(str, enum.Enum):
    """Types of entities that can be reviewed."""

    COMPANY = "company"
    RESTAURANT = "restaurant"
    RENTAL_PROPERTY = "rental_property"
    HOTEL = "hotel"
    PLACE = "place"
    SERVICE = "service"
    PRODUCT = "product"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class Platform(str, enum.Enum):
    """Platforms where reviews are sourced from."""

    GOOGLE = "google"
    YELP = "yelp"
    TRIPADVISOR = "tripadvisor"
    TRUSTPILOT = "trustpilot"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    REDDIT = "reddit"
    ZILLOW = "zillow"
    AIRBNB = "airbnb"
    BOOKING = "booking"
    AMAZON = "amazon"
    GLASSDOOR = "glassdoor"
    BBB = "bbb"  # Better Business Bureau
    FOURSQUARE = "foursquare"
    YOUTUBE = "youtube"
    APPSTORE = "appstore"
    PLAYSTORE = "playstore"
    OTHER = "other"


class Review(Base):
    """
    Review model for aggregating reviews from multiple platforms.

    This model is designed to store reviews from various sources including
    social media, business review sites, and specialized platforms.
    """

    __tablename__ = "reviews"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Entity information (what is being reviewed)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType), nullable=False, index=True
    )
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    entity_identifier: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )  # External ID (Google Place ID, etc.)

    # Platform information
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform), nullable=False, index=True
    )
    platform_review_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )  # Unique constraint to prevent duplicates

    # Reviewer information
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    reviewer_identifier: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    reviewer_profile_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Review content
    rating: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Some platforms don't have ratings

    review_title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    review_text: Mapped[str] = mapped_column(Text, nullable=False)

    review_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )  # Link to original review

    # Temporal data
    review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Engagement metrics
    helpful_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )  # Likes, upvotes, helpful marks

    # Verification and authenticity
    verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )  # Verified purchase/visit

    # Sentiment analysis (to be populated by ML pipeline)
    sentiment_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # -1.0 to 1.0

    # Business response (if available)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    response_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Media attachments
    images: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )  # Array of image URLs

    # Additional platform-specific data (flexible JSON storage)
    # Note: 'metadata' is reserved in SQLAlchemy, so we use 'extra_data'
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, name="metadata"
    )  # Store any platform-specific fields

    # Soft delete and status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), index=True
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, platform={self.platform}, entity={self.entity_name}, rating={self.rating})>"
