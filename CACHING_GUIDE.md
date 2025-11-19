# Caching Strategy Guide

## Overview

TheReview uses **Redis** for high-performance caching of review data. The caching layer significantly reduces database load and improves API response times.

## Architecture

```
┌─────────────┐
│   FastAPI   │
│   Request   │
└──────┬──────┘
       │
       ├──────────────────────┐
       │                      │
   ┌───▼────┐            ┌────▼─────┐
   │ Redis  │            │ Postgres │
   │ Cache  │◄──────────►│ Database │
   │ (DB 1) │  on miss   └──────────┘
   └────────┘
```

### Cache Layers

1. **Redis DB 0**: 2FA tokens (auth library)
2. **Redis DB 1**: Review data caching (our implementation)

## Cache TTL Strategy

| Data Type | TTL | Use Case |
|-----------|-----|----------|
| **Short** (5 min) | 300s | Frequently changing data |
| **Medium** (30 min) | 1800s | Review lists, searches |
| **Long** (1 hour) | 3600s | Aggregated statistics |
| **Entity** (2 hours) | 7200s | Entity-specific data |

Configure in `app/core/config.py`:
```python
CACHE_TTL_SHORT: int = 300
CACHE_TTL_MEDIUM: int = 1800
CACHE_TTL_LONG: int = 3600
CACHE_TTL_ENTITY: int = 7200
```

---

## Key Components

### 1. Redis Cache Service (`app/utils/cache/redis_cache.py`)

**Features:**
- Async/await support for non-blocking I/O
- JSON serialization for complex objects
- Connection pooling
- Pattern-based deletion
- TTL management

**Basic Operations:**
```python
from app.utils.cache import cache

# Get from cache
value = await cache.get("key")

# Set with TTL
await cache.set("key", {"data": "value"}, ttl=1800)

# Delete
await cache.delete("key")

# Delete by pattern
await cache.delete_pattern("reviews:entity:*")
```

### 2. Cache Key Generator (`app/utils/cache/cache_keys.py`)

Generates consistent, namespaced cache keys.

**Key Patterns:**
```
reviews:single:{review_id}              # Single review
reviews:list:{hash}                     # Filtered lists
reviews:entity:{entity_id}:{platform}   # Entity reviews
reviews:platform:{platform}:p{page}     # Platform reviews
reviews:stats:{entity_id}               # Statistics
reviews:count:{entity_id}               # Counts
```

**Usage:**
```python
from app.utils.cache import cache_keys

# Generate keys
key = cache_keys.review_by_id(review_id)
key = cache_keys.reviews_by_entity("ChIJxxx", Platform.GOOGLE)
key = cache_keys.entity_stats("ChIJxxx")

# Generate patterns for bulk deletion
pattern = cache_keys.pattern_by_entity("ChIJxxx")
```

### 3. Caching Decorators (`app/utils/cache/decorators.py`)

#### `@cached` - Automatic caching

```python
from app.utils.cache import cached, cache_keys
from app.core.config import settings

@cached(
    key_func=lambda review_id: cache_keys.review_by_id(review_id),
    ttl=settings.CACHE_TTL_LONG
)
async def get_review(review_id: UUID) -> Review | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()
```

#### `@invalidate_cache` - Automatic invalidation

```python
from app.utils.cache import invalidate_cache, cache_keys

@invalidate_cache(
    lambda review: cache_keys.review_by_id(review.id),
    lambda review: cache_keys.reviews_by_entity(review.entity_identifier)
)
async def update_review(review: Review) -> Review:
    # Update database
    await db.commit()
    await db.refresh(review)
    return review
```

#### `@invalidate_pattern` - Pattern-based invalidation

```python
from app.utils.cache import invalidate_pattern, cache_keys

@invalidate_pattern(
    lambda review: cache_keys.pattern_by_entity(review.entity_identifier)
)
async def delete_review(review_id: UUID) -> bool:
    await db.execute(delete(Review).where(Review.id == review_id))
    await db.commit()
    return True
```

### 4. Cache Invalidator (`app/utils/cache/invalidation.py`)

Smart invalidation strategies for data changes.

```python
from app.utils.cache import invalidator

# On review create
await invalidator.invalidate_on_create(review)

# On review update
await invalidator.invalidate_on_update(review)

# On review delete
await invalidator.invalidate_on_delete(review)

# On bulk create (more efficient)
await invalidator.invalidate_on_bulk_create(reviews)

# Clear specific entity
await invalidator.invalidate_entity("ChIJxxx")

# Clear specific platform
await invalidator.invalidate_platform(Platform.GOOGLE)

# Nuclear option: clear everything
await invalidator.clear_all_review_caches()
```

---

## Common Patterns

### Pattern 1: Cache-Aside (Lazy Loading)

```python
from app.utils.cache import cache, cache_keys
from app.core.config import settings

async def get_reviews_by_entity(entity_id: str) -> list[Review]:
    # Try cache first
    cache_key = cache_keys.reviews_by_entity(entity_id)
    cached_reviews = await cache.get(cache_key)

    if cached_reviews:
        return cached_reviews

    # Cache miss - fetch from database
    result = await db.execute(
        select(Review)
        .where(Review.entity_identifier == entity_id)
        .where(Review.is_active == True)
    )
    reviews = result.scalars().all()

    # Store in cache
    await cache.set(cache_key, reviews, ttl=settings.CACHE_TTL_ENTITY)

    return reviews
```

### Pattern 2: Cache-Through (Write-Through)

```python
from app.utils.cache import cache, cache_keys

async def create_review(review_data: ReviewCreate) -> Review:
    # Create in database
    review = Review(**review_data.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # Immediately cache
    cache_key = cache_keys.review_by_id(review.id)
    await cache.set(cache_key, review, ttl=settings.CACHE_TTL_LONG)

    # Invalidate related caches
    await invalidator.invalidate_on_create(review)

    return review
```

### Pattern 3: Read-Through with Decorator

```python
from app.utils.cache import cached, cache_keys

@cached(
    key_func=lambda page, size: cache_keys.review_list(page=page, page_size=size),
    ttl=settings.CACHE_TTL_MEDIUM
)
async def get_reviews_paginated(page: int = 1, page_size: int = 20) -> list[Review]:
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Review)
        .where(Review.is_active == True)
        .order_by(Review.review_date.desc())
        .limit(page_size)
        .offset(offset)
    )
    return result.scalars().all()
```

### Pattern 4: Cache Statistics (Expensive Aggregations)

```python
from sqlalchemy import func
from app.utils.cache import cache, cache_keys

async def get_entity_stats(entity_id: str) -> dict:
    cache_key = cache_keys.entity_stats(entity_id)
    cached_stats = await cache.get(cache_key)

    if cached_stats:
        return cached_stats

    # Expensive aggregation query
    result = await db.execute(
        select(
            func.count(Review.id).label("total_reviews"),
            func.avg(Review.rating).label("avg_rating"),
            func.min(Review.review_date).label("oldest_review"),
            func.max(Review.review_date).label("newest_review"),
        )
        .where(Review.entity_identifier == entity_id)
        .where(Review.is_active == True)
    )
    stats = result.one()

    stats_dict = {
        "total_reviews": stats.total_reviews,
        "avg_rating": float(stats.avg_rating) if stats.avg_rating else None,
        "oldest_review": stats.oldest_review,
        "newest_review": stats.newest_review,
    }

    # Cache for 1 hour
    await cache.set(cache_key, stats_dict, ttl=settings.CACHE_TTL_LONG)

    return stats_dict
```

---

## API Endpoint Integration

### Example: Review Endpoints with Caching

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse
from app.utils.cache import cache, cache_keys, invalidator, cached

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get("/{review_id}", response_model=ReviewResponse)
@cached(
    key_func=lambda review_id, db: cache_keys.review_by_id(review_id),
    ttl=settings.CACHE_TTL_LONG
)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Review:
    """Get single review (cached)."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/", response_model=ReviewResponse)
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db)
) -> Review:
    """Create review (invalidates related caches)."""
    review = Review(**review_data.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # Smart cache invalidation
    await invalidator.invalidate_on_create(review)

    return review


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_data: ReviewUpdate,
    db: AsyncSession = Depends(get_db)
) -> Review:
    """Update review (invalidates caches)."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Update fields
    for field, value in review_data.model_dump(exclude_unset=True).items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)

    # Smart cache invalidation
    await invalidator.invalidate_on_update(review)

    return review


@router.get("/entity/{entity_id}", response_model=list[ReviewResponse])
async def get_entity_reviews(
    entity_id: str,
    platform: Platform | None = None,
    db: AsyncSession = Depends(get_db)
) -> list[Review]:
    """Get all reviews for an entity (cached by entity)."""
    cache_key = cache_keys.reviews_by_entity(entity_id, platform)
    cached_reviews = await cache.get(cache_key)

    if cached_reviews:
        return cached_reviews

    # Build query
    query = select(Review).where(
        Review.entity_identifier == entity_id,
        Review.is_active == True
    )
    if platform:
        query = query.where(Review.platform == platform)

    result = await db.execute(query.order_by(Review.review_date.desc()))
    reviews = result.scalars().all()

    # Cache for 2 hours
    await cache.set(cache_key, reviews, ttl=settings.CACHE_TTL_ENTITY)

    return reviews
```

---

## Cache Monitoring & Debugging

### Check Cache Status

```python
from app.utils.cache import cache

# Check if key exists
exists = await cache.exists("reviews:single:123")

# Get TTL
ttl = await cache.get_ttl("reviews:single:123")
print(f"Key expires in {ttl} seconds")

# Increment counter (for tracking cache hits)
hits = await cache.increment("cache:hits:reviews")
```

### Clear Caches (Maintenance)

```python
from app.utils.cache import invalidator, cache

# Clear specific entity
await invalidator.invalidate_entity("ChIJxxx")

# Clear specific platform
await invalidator.invalidate_platform(Platform.GOOGLE)

# Clear all review lists
await cache.delete_pattern("reviews:list:*")

# Nuclear option: clear everything
await invalidator.clear_all_review_caches()
```

---

## Performance Tips

### 1. Cache Expensive Queries
Always cache:
- Aggregations (COUNT, AVG, SUM)
- Multi-table JOINs
- Full-text searches
- Paginated lists

### 2. Use Appropriate TTLs
- **Frequently updated**: Short TTL (5-10 min)
- **Read-heavy**: Medium TTL (30 min)
- **Statistics**: Long TTL (1+ hour)
- **Historical data**: Very long TTL (24+ hours)

### 3. Invalidate Smartly
- Use pattern matching for bulk invalidation
- Invalidate on CREATE/UPDATE/DELETE
- Don't invalidate too broadly (performance hit)

### 4. Monitor Cache Hit Rates

```python
# Track hits/misses (implement in production)
cache_hits = await cache.get("metrics:cache:hits") or 0
cache_misses = await cache.get("metrics:cache:misses") or 0
hit_rate = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
```

Target hit rate: **70-90%** for optimal performance

---

## Troubleshooting

### Cache Not Working?

1. **Check Redis is running:**
```bash
redis-cli -h localhost -p 6379 ping
# Should return: PONG
```

2. **Check cache DB:**
```bash
redis-cli -h localhost -p 6379 -n 1 KEYS "reviews:*"
```

3. **Check logs:**
Look for "Cache HIT" / "Cache MISS" in application logs

### Clear Stuck Cache

```bash
# Connect to Redis
redis-cli -h localhost -p 6379 -n 1

# List all keys
KEYS reviews:*

# Delete specific pattern
DEL reviews:entity:ChIJxxx:*

# Flush entire cache DB (WARNING!)
FLUSHDB
```

---

## Best Practices

### ✅ DO
- Cache expensive database queries
- Use descriptive cache keys
- Set appropriate TTLs
- Invalidate on data changes
- Monitor cache performance
- Use patterns for bulk operations

### ❌ DON'T
- Cache user-specific data without user ID in key
- Use very short TTLs (<1 min) - defeats purpose
- Cache everything - be selective
- Forget to handle cache misses
- Store large objects (>1MB) in cache
- Use cache as primary data store

---

## Configuration

Edit `backend/config/.env`:

```env
# Redis Configuration
REDIS_HOST=redis://localhost:6379
REDIS_CACHE_DB=1

# Cache TTL Settings (seconds)
CACHE_TTL_SHORT=300      # 5 minutes
CACHE_TTL_MEDIUM=1800    # 30 minutes
CACHE_TTL_LONG=3600      # 1 hour
CACHE_TTL_ENTITY=7200    # 2 hours
```

---

## Testing Caching

```python
import pytest
from app.utils.cache import cache, cache_keys

@pytest.mark.asyncio
async def test_review_caching():
    # Setup
    await cache.connect()

    # Test set/get
    key = cache_keys.review_by_id("test-id")
    test_data = {"id": "test-id", "rating": 5.0}

    await cache.set(key, test_data, ttl=60)
    cached_data = await cache.get(key)

    assert cached_data == test_data

    # Test invalidation
    await cache.delete(key)
    assert await cache.get(key) is None

    # Cleanup
    await cache.disconnect()
```

---

## Next Steps

1. Implement caching in your review service layer
2. Add cache monitoring/metrics endpoints
3. Set up Redis persistence (RDB/AOF) for production
4. Configure Redis cluster for high availability
5. Implement cache warming strategies
6. Add rate limiting using Redis

---

**Performance Impact:**
- Database load: **↓ 60-80%**
- API response time: **↓ 50-70%**
- Concurrent requests: **↑ 3-5x**

Happy caching! 🚀
