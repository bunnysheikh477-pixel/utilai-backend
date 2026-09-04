import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.seed_data import CATEGORIES, PLANS, TOOLS
from app.models.enums import UserRole
from app.utils.helpers import new_id, utcnow

logger = logging.getLogger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    await db["tools"].create_index("slug", unique=True)
    await db["tools"].create_index([("category_slug", 1), ("status", 1)])
    await db["tools"].create_index([("status", 1), ("is_popular", -1)])
    await db["categories"].create_index("slug", unique=True)
    await db["users"].create_index("email", unique=True)
    await db["tool_usage"].create_index([("tool_id", 1), ("created_at", -1)])
    await db["tool_jobs"].create_index([("status", 1), ("created_at", 1)])
    await db["analytics_events"].create_index([("event_type", 1), ("created_at", -1)])


async def sync_seed(db: AsyncIOMotorDatabase) -> None:
    """Upsert categories and tools from seed_data so new entries appear without a full reset."""
    for cat in CATEGORIES:
        slug = cat["slug"]
        await db["categories"].update_one({"slug": slug}, {"$set": cat}, upsert=True)

    for tool in TOOLS:
        slug = tool["slug"]
        await db["tools"].update_one({"slug": slug}, {"$set": tool}, upsert=True)

    logger.info("Synced %d categories and %d tools from seed", len(CATEGORIES), len(TOOLS))


async def init_db(db: AsyncIOMotorDatabase) -> None:
    settings = get_settings()
    await create_indexes(db)

    if await db["categories"].count_documents({}) == 0:
        await db["categories"].insert_many(CATEGORIES)
        logger.info("Seeded %d categories", len(CATEGORIES))

    if await db["tools"].count_documents({}) == 0:
        await db["tools"].insert_many(TOOLS)
        logger.info("Seeded %d tools", len(TOOLS))

    await sync_seed(db)

    if await db["plans"].count_documents({}) == 0:
        await db["plans"].insert_many(PLANS)

    admin = await db["users"].find_one({"email": settings.SUPERADMIN_EMAIL.lower()})
    if not admin:
        await db["users"].insert_one({
            "_id": new_id(),
            "email": settings.SUPERADMIN_EMAIL.lower(),
            "password_hash": hash_password(settings.SUPERADMIN_PASSWORD),
            "full_name": "Super Admin",
            "role": UserRole.SUPER_ADMIN.value,
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        })
        logger.info("Created super admin: %s", settings.SUPERADMIN_EMAIL)

    if await db["ad_configs"].count_documents({}) == 0:
        await db["ad_configs"].insert_one({
            "_id": "default",
            "enabled": True,
            "placements": {
                "tool-top": True,
                "tool-bottom": True,
                "sidebar": True,
                "in-content": False,
            },
            "updated_at": utcnow(),
        })
