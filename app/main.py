from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.api.v1 import reviews , authentication , user
from app.core.auth.auth_setup import create_auth_service
from app.utils.logger import get_logger
from app.utils.mongo.mongo import connect_to_mongo, get_db, close_mongo_connection

logger = get_logger("Main", log_to_std_out=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager.

    On startup:
      - Connects to MongoDB.
      - Initializes AuthService (with Redis 2FA or mock).

    On shutdown:
      - Closes MongoDB connection.
    """
    await connect_to_mongo()
    database = await get_db()
    app.state.auth_service = create_auth_service(database)
    logger.info("Application startup complete")
    yield
    await close_mongo_connection()
    logger.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Used for auto IP detection
@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(authentication.router)
app.include_router(reviews.router)
app.include_router(user.router)

