from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import authentication, reviews, user
from app.core.auth.auth_setup import create_auth_service
from app.db.postgres import close_db, init_db
from app.utils.cache import cache
from app.utils.logger import get_logger
from app.utils.mongo.mongo import close_mongo_connection, connect_to_mongo, get_db
from app.utils.telemetry import setup_telemetry

logger = get_logger("Main", log_to_std_out=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager.

    On startup:
      - Connects to MongoDB (for user data).
      - Connects to PostgreSQL (for review data).
      - Initializes AuthService (with Redis 2FA or mock).

    On shutdown:
      - Closes MongoDB connection.
      - Closes PostgreSQL connection.
    """
    # Connect to MongoDB for user data
    await connect_to_mongo()
    database = await get_db()
    app.state.auth_service = create_auth_service(database)
    logger.info("MongoDB connection established")

    # Initialize PostgreSQL for review data
    # Note: Tables are created via Alembic migrations, not here
    # await init_db()  # Uncomment only for development/testing
    logger.info("PostgreSQL connection pool initialized")

    # Initialize Redis cache for review caching
    await cache.connect()
    logger.info("Redis cache connection established")

    logger.info("Application startup complete")
    yield

    # Cleanup connections
    await close_mongo_connection()
    logger.info("MongoDB connection closed")

    await close_db()
    logger.info("PostgreSQL connection pool closed")

    await cache.disconnect()
    logger.info("Redis cache connection closed")

    logger.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)

# Set up OpenTelemetry instrumentation
setup_telemetry(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Simple health check for Docker/K8s."""
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are ready.
    Used by Kubernetes/Docker to know when service is ready to accept traffic.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
    }

    # Check MongoDB
    try:
        database = await get_db()
        await database.command("ping")
        health_status["checks"]["mongodb"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["mongodb"] = f"error: {str(e)}"

    # Check PostgreSQL
    try:
        from app.db.postgres import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["postgres"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["postgres"] = f"error: {str(e)}"

    # Check Redis
    try:
        from app.utils.cache import cache

        await cache.set("health_check", "ok", ttl=10)
        result = await cache.get("health_check")
        if result == "ok":
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["status"] = "unhealthy"
            health_status["checks"]["redis"] = "error: cache not working"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"error: {str(e)}"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return health_status, status_code


@app.get("/health/live")
async def liveness_check():
    """
    Liveness check - verifies application is alive.
    Used by Kubernetes/Docker to know if container should be restarted.
    """
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


app.include_router(authentication.router)
app.include_router(reviews.router)
app.include_router(user.router)
