# Review Data Model Schema

## Table: `reviews`

### Overview
Comprehensive review aggregation model supporting multiple platforms and entity types.

---

## Fields Reference

### Primary Key
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key, auto-generated |

### Entity Information (What is being reviewed)
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `entity_type` | ENUM | ✅ | ✅ | Type of entity (restaurant, company, etc.) |
| `entity_name` | String(500) | ✅ | ✅ | Name of the entity |
| `entity_identifier` | String(255) | ❌ | ✅ | External ID (Google Place ID, etc.) |

### Platform Information
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `platform` | ENUM | ✅ | ✅ | Source platform (google, yelp, etc.) |
| `platform_review_id` | String(255) | ✅ | ✅ (UNIQUE) | Unique review ID on source platform |

### Reviewer Information
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `reviewer_name` | String(255) | ❌ | ❌ | Name of reviewer |
| `reviewer_identifier` | String(255) | ❌ | ✅ | User ID on source platform |
| `reviewer_profile_url` | String(1000) | ❌ | ❌ | URL to reviewer's profile |

### Review Content
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `rating` | Float | ❌ | ❌ | Rating (0-5), null if platform has no ratings |
| `review_title` | String(500) | ❌ | ❌ | Title/subject of review |
| `review_text` | Text | ✅ | ❌ | Main review content |
| `review_url` | String(1000) | ❌ | ❌ | Link to original review |

### Temporal Data
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `review_date` | DateTime(TZ) | ✅ | ✅ | When review was posted on platform |
| `scraped_at` | DateTime(TZ) | ✅ | ❌ | When we collected the review |

### Engagement Metrics
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `helpful_count` | Integer | ✅ | 0 | Likes/upvotes/helpful marks |

### Verification & AI
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `verified` | Boolean | ✅ | false | Verified purchase/visit status |
| `sentiment_score` | Float | ❌ | null | AI sentiment score (-1.0 to 1.0) |

### Business Response
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `response_text` | Text | ❌ | Business/owner response to review |
| `response_date` | DateTime(TZ) | ❌ | When response was posted |

### Media & Metadata
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `images` | Array[String] | ❌ | URLs to review images |
| `extra_data` | JSONB | ❌ | Platform-specific metadata |

### Status & Audit
| Field | Type | Required | Indexed | Default | Description |
|-------|------|----------|---------|---------|-------------|
| `is_active` | Boolean | ✅ | ✅ | true | Soft delete flag |
| `created_at` | DateTime(TZ) | ✅ | ❌ | NOW | Record creation timestamp |
| `updated_at` | DateTime(TZ) | ✅ | ❌ | NOW | Last update timestamp |

---

## Enums

### EntityType
```python
class EntityType(str, enum.Enum):
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
```

### Platform
```python
class Platform(str, enum.Enum):
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
    BBB = "bbb"               # Better Business Bureau
    FOURSQUARE = "foursquare"
    YOUTUBE = "youtube"
    APPSTORE = "appstore"
    PLAYSTORE = "playstore"
    OTHER = "other"
```

---

## Indexes

Optimized for common query patterns:

1. **Entity Queries**
   - `entity_type` - Filter by type
   - `entity_name` - Search by name
   - `entity_identifier` - Lookup by external ID

2. **Platform Queries**
   - `platform` - Filter by source platform
   - `platform_review_id` - Unique constraint & fast lookup

3. **Reviewer Queries**
   - `reviewer_identifier` - Track reviews by user

4. **Temporal Queries**
   - `review_date` - Time-series analysis

5. **Status Filtering**
   - `is_active` - Exclude soft-deleted records

---

## Constraints

- **Primary Key**: `id` (UUID)
- **Unique Constraint**: `platform_review_id` (prevents duplicate reviews)

---

## Example Use Cases

### 1. Restaurant Reviews from Google
```python
Review(
    entity_type=EntityType.RESTAURANT,
    entity_name="Joe's Pizza",
    entity_identifier="ChIJxxx",  # Google Place ID
    platform=Platform.GOOGLE,
    platform_review_id="google_review_123",
    reviewer_name="John Doe",
    rating=4.5,
    review_text="Great pizza, friendly service!",
    review_date=datetime(2025, 1, 15),
    verified=True,
    images=["https://...img1.jpg"]
)
```

### 2. Company Review from Glassdoor
```python
Review(
    entity_type=EntityType.COMPANY,
    entity_name="TechCorp Inc",
    platform=Platform.GLASSDOOR,
    platform_review_id="glassdoor_456",
    reviewer_name="Anonymous",
    rating=3.5,
    review_title="Good benefits, but...",
    review_text="Decent place to work...",
    review_date=datetime(2025, 1, 10),
    verified=True,
    extra_data={
        "position": "Software Engineer",
        "employment_status": "Current Employee"
    }
)
```

### 3. Rental Property from Zillow
```python
Review(
    entity_type=EntityType.RENTAL_PROPERTY,
    entity_name="Sunset Apartments",
    entity_identifier="zillow_property_789",
    platform=Platform.ZILLOW,
    platform_review_id="zillow_review_789",
    reviewer_name="Jane Smith",
    rating=5.0,
    review_text="Beautiful apartment, great location!",
    review_date=datetime(2025, 1, 5),
    response_text="Thank you for the kind review!",
    response_date=datetime(2025, 1, 6)
)
```

### 4. Product Review from Amazon
```python
Review(
    entity_type=EntityType.PRODUCT,
    entity_name="Wireless Headphones XYZ",
    entity_identifier="B08XXXX",  # ASIN
    platform=Platform.AMAZON,
    platform_review_id="amazon_review_999",
    reviewer_name="Mike Johnson",
    rating=4.0,
    review_title="Good sound quality",
    review_text="Battery life could be better...",
    review_date=datetime(2025, 1, 12),
    verified=True,
    helpful_count=15,
    images=["https://...product_img.jpg"],
    extra_data={
        "verified_purchase": True,
        "vine_voice": False
    }
)
```

---

## Query Examples

### Get All Restaurant Reviews
```python
reviews = await db.execute(
    select(Review)
    .where(Review.entity_type == EntityType.RESTAURANT)
    .where(Review.is_active == True)
)
```

### Get High-Rated Reviews from Google
```python
reviews = await db.execute(
    select(Review)
    .where(Review.platform == Platform.GOOGLE)
    .where(Review.rating >= 4.0)
    .where(Review.is_active == True)
    .order_by(Review.review_date.desc())
)
```

### Get All Reviews for Specific Entity
```python
reviews = await db.execute(
    select(Review)
    .where(Review.entity_identifier == "ChIJxxx")
    .where(Review.is_active == True)
    .order_by(Review.review_date.desc())
)
```

### Calculate Average Rating
```python
from sqlalchemy import func

result = await db.execute(
    select(func.avg(Review.rating))
    .where(Review.entity_name == "Joe's Pizza")
    .where(Review.is_active == True)
)
avg_rating = result.scalar()
```

---

## Migration ID

**Initial Migration**: `69116d97f864_create_reviews_table_with_multi_.py`

Run with: `uv run alembic upgrade head`
