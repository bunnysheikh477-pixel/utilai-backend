from fastapi import APIRouter

from app.api.v1 import admin, auth, categories, tools

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
