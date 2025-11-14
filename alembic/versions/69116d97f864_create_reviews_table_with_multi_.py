"""Create reviews table with multi-platform aggregation support

Revision ID: 69116d97f864
Revises:
Create Date: 2025-11-11 14:51:30.452104

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "69116d97f864"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create reviews table."""
    # Create entity_type enum
    entity_type_enum = postgresql.ENUM(
        "company",
        "restaurant",
        "rental_property",
        "hotel",
        "place",
        "service",
        "product",
        "healthcare",
        "education",
        "entertainment",
        "other",
        name="entitytype",
        create_type=True,
    )

    # Create platform enum
    platform_enum = postgresql.ENUM(
        "google",
        "yelp",
        "tripadvisor",
        "trustpilot",
        "twitter",
        "linkedin",
        "facebook",
        "reddit",
        "zillow",
        "airbnb",
        "booking",
        "amazon",
        "glassdoor",
        "bbb",
        "foursquare",
        "youtube",
        "appstore",
        "playstore",
        "other",
        name="platform",
        create_type=True,
    )

    # Create reviews table
    op.create_table(
        "reviews",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Entity information
        sa.Column("entity_type", entity_type_enum, nullable=False),
        sa.Column("entity_name", sa.String(length=500), nullable=False),
        sa.Column("entity_identifier", sa.String(length=255), nullable=True),
        # Platform information
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("platform_review_id", sa.String(length=255), nullable=False),
        # Reviewer information
        sa.Column("reviewer_name", sa.String(length=255), nullable=True),
        sa.Column("reviewer_identifier", sa.String(length=255), nullable=True),
        sa.Column("reviewer_profile_url", sa.String(length=1000), nullable=True),
        # Review content
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_title", sa.String(length=500), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("review_url", sa.String(length=1000), nullable=True),
        # Temporal data
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        # Engagement metrics
        sa.Column("helpful_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        # Verification
        sa.Column("verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        # Sentiment analysis
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        # Business response
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("response_date", sa.DateTime(timezone=True), nullable=True),
        # Media attachments
        sa.Column("images", postgresql.ARRAY(sa.String()), nullable=True),
        # Additional platform-specific data
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Soft delete and status
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        # Audit timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform_review_id"),
    )

    # Create indexes for common queries
    op.create_index("ix_reviews_entity_type", "reviews", ["entity_type"])
    op.create_index("ix_reviews_entity_name", "reviews", ["entity_name"])
    op.create_index("ix_reviews_entity_identifier", "reviews", ["entity_identifier"])
    op.create_index("ix_reviews_platform", "reviews", ["platform"])
    op.create_index("ix_reviews_platform_review_id", "reviews", ["platform_review_id"])
    op.create_index("ix_reviews_reviewer_identifier", "reviews", ["reviewer_identifier"])
    op.create_index("ix_reviews_review_date", "reviews", ["review_date"])
    op.create_index("ix_reviews_is_active", "reviews", ["is_active"])


def downgrade() -> None:
    """Downgrade schema - drop reviews table."""
    # Drop indexes
    op.drop_index("ix_reviews_is_active", table_name="reviews")
    op.drop_index("ix_reviews_review_date", table_name="reviews")
    op.drop_index("ix_reviews_reviewer_identifier", table_name="reviews")
    op.drop_index("ix_reviews_platform_review_id", table_name="reviews")
    op.drop_index("ix_reviews_platform", table_name="reviews")
    op.drop_index("ix_reviews_entity_identifier", table_name="reviews")
    op.drop_index("ix_reviews_entity_name", table_name="reviews")
    op.drop_index("ix_reviews_entity_type", table_name="reviews")

    # Drop table
    op.drop_table("reviews")

    # Drop enums
    sa.Enum(name="platform").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="entitytype").drop(op.get_bind(), checkfirst=True)
