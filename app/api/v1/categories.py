from fastapi import APIRouter

from app.core.database import get_database
from app.services.tool_service import CategoryService, ToolService

router = APIRouter()


@router.get("")
async def list_categories():
    db = get_database()
    cats = await CategoryService(db).list_all()
    for cat in cats:
        cat["tools"] = await ToolService(db).list_published(cat["slug"])
    return {"success": True, "data": cats}


@router.get("/{slug}")
async def get_category(slug: str):
    db = get_database()
    cat = await CategoryService(db).get_by_slug(slug)
    if not cat:
        return {"success": False, "message": "Category not found"}
    cat["tools"] = await ToolService(db).list_published(slug)
    return {"success": True, "data": cat}
