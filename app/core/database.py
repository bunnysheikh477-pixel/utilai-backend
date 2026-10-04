import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client = None
_db: Optional[AsyncIOMotorDatabase] = None
_using_memory = False


async def connect_db() -> AsyncIOMotorDatabase:
    global _client, _db, _using_memory
    settings = get_settings()
    if settings.USE_MEMORY_DB and settings.DEBUG:
        logger.warning("USE_MEMORY_DB=true - using in-memory MongoDB for local development")
        return _memory_db(settings.MONGODB_DATABASE)
    try:
        client = AsyncIOMotorClient(settings.DATABASE_URL, serverSelectionTimeoutMS=8000)
        await client.admin.command("ping")
        _client = client
        _db = client[settings.MONGODB_DATABASE]
        _using_memory = False
        logger.info("Connected to MongoDB database %s", settings.MONGODB_DATABASE)
        return _db
    except Exception as exc:
        logger.error(
            "MongoDB connection failed (%s). Check DATABASE_URL and confirm MongoDB is running.",
            type(exc).__name__,
        )
        raise RuntimeError(
            "MongoDB is unavailable. Set USE_MEMORY_DB=true only for temporary development, "
            "or configure a working DATABASE_URL."
        ) from exc


def _memory_db(name: str) -> AsyncIOMotorDatabase:
    global _client, _db, _using_memory
    from mongomock_motor import AsyncMongoMockClient

    _client = AsyncMongoMockClient()
    _db = _client[name]
    _using_memory = True
    return _db


async def close_db() -> None:
    global _client, _db, _using_memory
    if _client is not None and not _using_memory:
        _client.close()
    _client = _db = None
    _using_memory = False


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


def is_using_memory_db() -> bool:
    return _using_memory
