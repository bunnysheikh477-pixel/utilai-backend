from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import serialize


class ToolService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def list_published(self, category: Optional[str] = None, popular: bool = False) -> list[dict]:
        query: dict[str, Any] = {"status": "published"}
        if category:
            query["category_slug"] = category
        if popular:
            query["is_popular"] = True
        cursor = self.db["tools"].find(query).sort("sort_order", 1)
        return [serialize(d) for d in await cursor.to_list(500)]  # type: ignore

    async def get_by_slug(self, category: str, slug: str) -> Optional[dict]:
        doc = await self.db["tools"].find_one({"category_slug": category, "slug": slug, "status": "published"})
        return serialize(doc)

    async def search(self, q: str, limit: int = 20) -> list[dict]:
        regex = {"$regex": q, "$options": "i"}
        cursor = self.db["tools"].find(
            {"status": "published", "$or": [{"name": regex}, {"short_description": regex}, {"keywords": regex}]}
        ).limit(limit)
        return [serialize(d) for d in await cursor.to_list(limit)]  # type: ignore

    async def track_view(self, slug: str) -> None:
        from app.utils.helpers import new_id, utcnow
        await self.db["analytics_events"].insert_one({
            "_id": new_id(), "event_type": "tool_view", "tool_slug": slug, "created_at": utcnow(),
        })
        await self.db["tools"].update_one({"slug": slug}, {"$inc": {"view_count": 1}})


class CategoryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def list_all(self) -> list[dict]:
        cursor = self.db["categories"].find({}).sort("sort_order", 1)
        return [serialize(d) for d in await cursor.to_list(50)]  # type: ignore

    async def get_by_slug(self, slug: str) -> Optional[dict]:
        return serialize(await self.db["categories"].find_one({"slug": slug}))
