from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import EntityType, Platform, Review
from app.schemas.review import ReviewCreate, ReviewUpdate


class ReviewService:
    """Service layer for review CRUD operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the service with a database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    # ═══════════════════════════════════════════════════════════════
    # CREATE OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    async def create_review(self, review_data: ReviewCreate) -> Review:
        """
        Create a new review.

        Args:
            review_data: Review creation data

        Returns:
            Created review object
        """
        # Create review instance from schema
        review = Review(**review_data.model_dump())
        review.scraped_at = datetime.now(UTC)

        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)

        return review

    async def bulk_create_reviews(self, reviews_data: list[ReviewCreate]) -> list[Review]:
        """
        Create multiple reviews efficiently.

        Args:
            reviews_data: List of review creation data

        Returns:
            List of created review objects
        """
        reviews = []
        for review_data in reviews_data:
            review = Review(**review_data.model_dump())
            review.scraped_at = datetime.now(UTC)
            reviews.append(review)

        self.db.add_all(reviews)
        await self.db.commit()

        # Refresh all to get generated IDs and timestamps
        for review in reviews:
            await self.db.refresh(review)

        return reviews

    # ═══════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    async def get_review_by_id(self, review_id: UUID) -> Review | None:
        """
        Get a single review by ID.

        Args:
            review_id: UUID of the review

        Returns:
            Review object or None if not found
        """
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_reviews(
        self,
        entity_type: EntityType | None = None,
        entity_name: str | None = None,
        entity_identifier: str | None = None,
        platform: Platform | None = None,
        min_rating: float | None = None,
        max_rating: float | None = None,
        verified_only: bool = False,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Review]:
        """
        Get reviews with optional filters.

        Args:
            entity_type: Filter by entity type
            entity_name: Filter by entity name (partial match)
            entity_identifier: Filter by exact entity identifier
            platform: Filter by platform
            min_rating: Minimum rating filter
            max_rating: Maximum rating filter
            verified_only: Only return verified reviews
            is_active: Filter by active status (default True)
            limit: Maximum number of reviews to return
            offset: Number of reviews to skip

        Returns:
            List of review objects
        """
        query = select(Review).where(Review.is_active == is_active)

        # Apply filters
        if entity_type:
            query = query.where(Review.entity_type == entity_type)

        if entity_name:
            query = query.where(Review.entity_name.ilike(f"%{entity_name}%"))

        if entity_identifier:
            query = query.where(Review.entity_identifier == entity_identifier)

        if platform:
            query = query.where(Review.platform == platform)

        if min_rating is not None:
            query = query.where(Review.rating >= min_rating)

        if max_rating is not None:
            query = query.where(Review.rating <= max_rating)

        if verified_only:
            query = query.where(Review.verified)

        # Order by most recent first
        query = query.order_by(Review.review_date.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_reviews_by_entity(
        self,
        entity_identifier: str,
        platform: Platform | None = None,
        limit: int = 100,
    ) -> list[Review]:
        """
        Get all reviews for a specific entity.

        Args:
            entity_identifier: The entity's identifier (e.g., Google Place ID)
            platform: Optional platform filter
            limit: Maximum number of reviews to return

        Returns:
            List of review objects
        """
        query = select(Review).where(
            Review.entity_identifier == entity_identifier,
            Review.is_active,
        )

        if platform:
            query = query.where(Review.platform == platform)

        query = query.order_by(Review.review_date.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_reviews_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        entity_type: EntityType | None = None,
        platform: Platform | None = None,
        min_rating: float | None = None,
    ) -> tuple[list[Review], int]:
        """
        Get paginated reviews with filters.

        Args:
            page: Page number (1-indexed)
            page_size: Number of reviews per page
            entity_type: Filter by entity type
            platform: Filter by platform
            min_rating: Minimum rating filter

        Returns:
            Tuple of (reviews list, total count)
        """
        # Build base query
        query = select(Review).where(Review.is_active)

        if entity_type:
            query = query.where(Review.entity_type == entity_type)
        if platform:
            query = query.where(Review.platform == platform)
        if min_rating is not None:
            query = query.where(Review.rating >= min_rating)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Get paginated results
        offset = (page - 1) * page_size
        query = query.order_by(Review.review_date.desc()).limit(page_size).offset(offset)

        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        return reviews, total

    async def count_reviews(
        self,
        entity_identifier: str | None = None,
        platform: Platform | None = None,
        is_active: bool = True,
    ) -> int:
        """
        Count reviews with optional filters.

        Args:
            entity_identifier: Filter by entity identifier
            platform: Filter by platform
            is_active: Filter by active status

        Returns:
            Count of reviews
        """
        query = select(func.count(Review.id)).where(Review.is_active == is_active)

        if entity_identifier:
            query = query.where(Review.entity_identifier == entity_identifier)

        if platform:
            query = query.where(Review.platform == platform)

        result = await self.db.execute(query)
        return result.scalar()

    # ═══════════════════════════════════════════════════════════════
    # UPDATE OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    async def update_review(
        self,
        review_id: UUID,
        review_data: ReviewUpdate,
    ) -> Review | None:
        """
        Update an existing review.

        Args:
            review_id: UUID of the review to update
            review_data: Updated review data

        Returns:
            Updated review object or None if not found
        """
        # Get existing review
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            return None

        # Update fields (only fields that were provided)
        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)

        # Update timestamp
        review.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(review)

        return review

    async def bulk_update_reviews(
        self,
        filters: dict,
        update_data: dict,
    ) -> int:
        """
        Update multiple reviews matching filters.

        Args:
            filters: Dictionary of filters (e.g., {"platform": Platform.GOOGLE})
            update_data: Dictionary of fields to update

        Returns:
            Number of reviews updated
        """
        stmt = update(Review)

        # Apply filters
        for key, value in filters.items():
            stmt = stmt.where(getattr(Review, key) == value)

        # Add update data
        update_data["updated_at"] = datetime.now(UTC)
        stmt = stmt.values(**update_data)

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount

    # ═══════════════════════════════════════════════════════════════
    # DELETE OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    async def delete_review(
        self,
        review_id: UUID,
        soft: bool = True,
    ) -> bool:
        """
        Delete a review (soft or hard delete).

        Soft delete: Mark as inactive (keeps data)
        Hard delete: Permanently remove from database

        Args:
            review_id: UUID of the review to delete
            soft: If True, soft delete. If False, hard delete.

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            return False

        if soft:
            # Soft delete - mark as inactive
            review.is_active = False
            review.updated_at = datetime.now(UTC)
            await self.db.commit()
        else:
            # Hard delete - remove from database
            await self.db.delete(review)
            await self.db.commit()

        return True

    async def bulk_delete_reviews(
        self,
        entity_identifier: str,
        platform: Platform | None = None,
        soft: bool = True,
    ) -> int:
        """
        Delete multiple reviews for an entity.

        Args:
            entity_identifier: Entity identifier
            platform: Optional platform filter
            soft: If True, soft delete. If False, hard delete.

        Returns:
            Number of reviews deleted
        """
        if soft:
            # Soft delete using update
            stmt = (
                update(Review)
                .where(Review.entity_identifier == entity_identifier)
                .values(is_active=False, updated_at=datetime.now(UTC))
            )

            if platform:
                stmt = stmt.where(Review.platform == platform)

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount
        else:
            # Hard delete
            stmt = delete(Review).where(
                Review.entity_identifier == entity_identifier
            )

            if platform:
                stmt = stmt.where(Review.platform == platform)

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount

    # ═══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════

    async def get_average_rating(self, entity_identifier: str) -> float | None:
        """
        Calculate average rating for an entity.

        Args:
            entity_identifier: Entity identifier

        Returns:
            Average rating or None if no reviews with ratings
        """
        result = await self.db.execute(
            select(func.avg(Review.rating))
            .where(Review.entity_identifier == entity_identifier)
            .where(Review.is_active)
            .where(Review.rating.isnot(None))
        )
        avg_rating = result.scalar()
        return float(avg_rating) if avg_rating else None

    async def get_platform_distribution(
        self, entity_identifier: str
    ) -> dict[str, int]:
        """
        Get count of reviews per platform for an entity.

        Args:
            entity_identifier: Entity identifier

        Returns:
            Dictionary mapping platform name to count
        """
        result = await self.db.execute(
            select(Review.platform, func.count(Review.id))
            .where(Review.entity_identifier == entity_identifier)
            .where(Review.is_active)
            .group_by(Review.platform)
        )

        return {row.platform.value: row[1] for row in result.all()}
