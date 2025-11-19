# Database Setup Guide

## Overview

TheReview uses a **dual-database architecture**:

- **MongoDB**: User data, authentication, and user-related operations
- **PostgreSQL**: Review aggregation data from multiple platforms

## PostgreSQL Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/)

### 2. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE thereview_reviews;

# Create user (optional)
CREATE USER thereview WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE thereview_reviews TO thereview;

# Exit
\q
```

### 3. Configure Environment Variables

Update `backend/config/.env`:

```env
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=thereview_reviews
```

### 4. Run Database Migrations

```bash
cd backend

# Run migrations to create tables
uv run alembic upgrade head

# Check migration status
uv run alembic current

# View migration history
uv run alembic history
```

## Review Data Model

The `reviews` table is designed for **multi-platform review aggregation** with the following features:

### Entity Types Supported
- Companies (businesses, corporations)
- Restaurants
- Rental Properties
- Hotels
- Places (general locations)
- Services
- Products
- Healthcare facilities
- Educational institutions
- Entertainment venues
- Other (flexible)

### Platforms Supported
- **Social Media**: Twitter, LinkedIn, Facebook, Reddit
- **Review Sites**: Google Reviews, Yelp, TripAdvisor, Trustpilot
- **Real Estate**: Zillow, Airbnb, Booking.com
- **E-Commerce**: Amazon
- **Employment**: Glassdoor
- **Business**: Better Business Bureau (BBB)
- **Location**: Foursquare
- **Media**: YouTube
- **App Stores**: Apple App Store, Google Play Store
- **Other**: Extensible for new platforms

### Key Features

#### 1. Comprehensive Review Data
- **Content**: Title, text, rating (0-5), images
- **Metadata**: Platform-specific data (JSONB)
- **URLs**: Original review URL, reviewer profile

#### 2. Entity Identification
- Entity name and type
- External identifiers (Google Place ID, business IDs, etc.)
- Cross-platform entity matching support

#### 3. Reviewer Information
- Name, profile URL
- Platform-specific identifier
- Verification status

#### 4. Temporal Tracking
- Review date (when posted on platform)
- Scraped date (when collected by us)
- Audit timestamps (created/updated)

#### 5. Engagement Metrics
- Helpful count (likes, upvotes)
- Business responses with dates

#### 6. AI/ML Ready
- Sentiment score field (-1.0 to 1.0)
- Prepared for sentiment analysis pipeline

#### 7. Soft Deletes
- `is_active` flag for soft deletion
- Never lose data, just mark as inactive

### Database Indexes

Optimized indexes for common queries:
- Entity type, name, identifier
- Platform and platform review ID
- Reviewer identifier
- Review date (time-series queries)
- Active status (filter deleted records)

## Working with Alembic Migrations

### Create a New Migration

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Your migration message"

# Create empty migration (manual)
uv run alembic revision -m "Your migration message"
```

### Apply Migrations

```bash
# Upgrade to latest
uv run alembic upgrade head

# Upgrade one revision
uv run alembic upgrade +1

# Downgrade one revision
uv run alembic downgrade -1

# Downgrade to specific revision
uv run alembic downgrade <revision_id>
```

### Migration Management

```bash
# Show current revision
uv run alembic current

# Show migration history
uv run alembic history --verbose

# Show pending migrations
uv run alembic heads
```

## Database Access in Code

### Using the Database Session

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db
from app.models.review import Review

@app.get("/reviews")
async def get_reviews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).limit(10))
    reviews = result.scalars().all()
    return reviews
```

### Creating Records

```python
from app.models.review import Review, EntityType, Platform

@app.post("/reviews")
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db)
):
    review = Review(
        entity_type=EntityType.RESTAURANT,
        entity_name="Joe's Pizza",
        platform=Platform.GOOGLE,
        platform_review_id="google_123456",
        review_text="Amazing pizza!",
        rating=5.0,
        review_date=datetime.now(timezone.utc),
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    return review
```

### Querying Records

```python
from sqlalchemy import select

# Simple query
result = await db.execute(
    select(Review).where(Review.platform == Platform.GOOGLE)
)
reviews = result.scalars().all()

# With filters
result = await db.execute(
    select(Review)
    .where(Review.entity_type == EntityType.RESTAURANT)
    .where(Review.rating >= 4.0)
    .where(Review.is_active == True)
    .order_by(Review.review_date.desc())
    .limit(20)
)
reviews = result.scalars().all()
```

## MongoDB Configuration

MongoDB is used for user data and authentication. Configuration:

```env
MONGODB_URL=mongodb://localhost:27017/
MONGO_DATABASE_NAME=THE-REVIEW-USERS
```

The application connects to both databases on startup via the FastAPI lifespan manager.

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

### Permission Denied

```bash
# Reset PostgreSQL password
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD 'new_password';
```

### Migration Errors

```bash
# Check Alembic current state
uv run alembic current

# Stamp database with current revision (if out of sync)
uv run alembic stamp head
```

### View Database Contents

```bash
# Connect to database
psql -U postgres -d thereview_reviews

# List tables
\dt

# Describe reviews table
\d reviews

# Query reviews
SELECT * FROM reviews LIMIT 5;
```

## Next Steps

1. **Set up PostgreSQL** locally using the instructions above
2. **Run migrations** to create the database schema
3. **Test the connection** by starting the FastAPI app
4. **Implement review scraping** services for different platforms
5. **Create CRUD endpoints** for reviews in `app/api/v1/reviews.py`
6. **Integrate with frontend** Flutter app

## Future Enhancements

- [ ] Full-text search using PostgreSQL's `tsvector`
- [ ] Materialized views for aggregated statistics
- [ ] Partitioning by date for better performance
- [ ] Replication setup for production
- [ ] Connection pooling optimization
- [ ] Redis caching layer for frequently accessed reviews
