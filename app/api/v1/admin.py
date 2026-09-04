from fastapi import APIRouter, Depends

from app.api.deps import get_super_admin
from app.core.database import get_database
from app.services.tool_service import ToolService
from app.utils.helpers import serialize, utcnow

router = APIRouter()


@router.get("/stats")
async def platform_stats(_=Depends(get_super_admin)):
    db = get_database()
    tools = await db["tools"].count_documents({"status": "published"})
    users = await db["users"].count_documents({})
    views = await db["analytics_events"].count_documents({"event_type": "tool_view"})
    completions = await db["analytics_events"].count_documents({"event_type": "tool_complete"})
    return {"success": True, "data": {"tools": tools, "users": users, "views": views, "completions": completions}}


@router.get("/tools")
async def admin_tools(_=Depends(get_super_admin)):
    db = get_database()
    cursor = db["tools"].find({}).sort("category_slug", 1)
    return {"success": True, "data": [serialize(d) for d in await cursor.to_list(500)]}


@router.put("/tools/{tool_id}")
async def update_tool(tool_id: str, body: dict, _=Depends(get_super_admin)):
    db = get_database()
    body["updated_at"] = utcnow()
    await db["tools"].update_one({"_id": tool_id}, {"$set": body})
    doc = serialize(await db["tools"].find_one({"_id": tool_id}))
    return {"success": True, "data": doc}


@router.get("/analytics/top-tools")
async def top_tools(_=Depends(get_super_admin)):
    db = get_database()
    pipeline = [
        {"$match": {"event_type": "tool_view"}},
        {"$group": {"_id": "$tool_slug", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 20},
    ]
    results = await db["analytics_events"].aggregate(pipeline).to_list(20)
    return {"success": True, "data": results}
