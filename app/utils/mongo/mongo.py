
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# --- 1. Use the Asynchronous Client ---
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection

from app.core.config import settings

logger = logging.getLogger("db_utils")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


# --- 2. Global Context to Hold the Connection ---
# This is better than a simple global variable for managing async connections.
class DBContext:
    client: AsyncIOMotorClient = None

db_context = DBContext()

# --- 3. Lifespan Functions for your main.py ---
# These functions will be called at application startup and shutdown.
async def connect_to_mongo():
    """Connects to the MongoDB database."""
    logger.info("Connecting to MongoDB...")
    uri = settings.MONGODB_URL
    db_context.client = AsyncIOMotorClient(uri)
    logger.info("MongoDB connection successful.")
    logger.debug(f"Connected to URI: {uri}")

async def close_mongo_connection():
    """Closes the MongoDB connection."""
    logger.info("Closing MongoDB connection...")
    db_context.client.close()

# --- 4. Correct Asynchronous Dependency ---
async def get_db() -> AsyncIOMotorClient:
    """
    FastAPI dependency to get the database instance.
    This is now an async function that provides the correct object.
    """
    if db_context.client is None:
        raise Exception("Database client not initialized. Call connect_to_mongo() on startup.")
   
    return db_context.client[settings.MONGO_DATABASE_NAME]


# --- 5. All Helper Functions Converted to Async ---
# Every function that touches the database is now an `async def`
# and uses `await` for the database call.

async def get_collection(collection_name: str) -> Collection:
    """Asynchronously retrieves a collection object from the database."""
    db = await get_db()
    return db[collection_name]

async def insert_one(doc: dict, collection_name: str, **kwargs) -> Any:
    """Asynchronously inserts a single document."""
    try:
        db = await get_db()
        result = await db[collection_name].insert_one(doc)
        logger.debug(f"Inserted doc with ID {result.inserted_id} into {collection_name}.")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Failed to insert doc into {collection_name}: {e}")
        return None


async def insert_many(docs: List[dict], collection_name: str) -> List[Any]:
    """Asynchronously inserts multiple documents."""
    try:
        db = await get_db()
        result = await db[collection_name].insert_many(docs)
        logger.debug(f"Inserted {len(result.inserted_ids)} docs into {collection_name}.")
        return result.inserted_ids
    except Exception as e:
        logger.error(f"Failed to insert many docs into {collection_name}: {e}")
        return []


async def find(item: dict = {}, collection_name: str = "schedule", limit: int = 1000) -> List[Dict]:
    """Asynchronously finds documents."""
    db = await get_db()
    # You must use .to_list() to get results from an async cursor
    cursor = db[collection_name].find(item)
    return await cursor.to_list(length=limit)

async def update_one(
    filter_query: dict,
    update_data: dict,
    collection_name: str,
    create_if_not_exists: bool = False,
):
    """Asynchronously updates a single document."""
    db = await get_db()
    result = await db[collection_name].update_one(
        filter_query, update=update_data, upsert=create_if_not_exists
    )
    logger.debug(f"Updated {result.modified_count} doc(s) in {collection_name} matching {filter_query}.")
    return result


async def delete_one(filter_query: dict, collection_name: str) -> bool:
    """Asynchronously deletes a single document."""
    db = await get_db()
    result = await db[collection_name].delete_one(filter_query)
    if result.deleted_count > 0:
        logger.debug(f"Deleted doc from {collection_name} matching {filter_query}.")
    return result.deleted_count > 0

