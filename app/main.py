from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import close_db, connect_db
from app.core.exceptions import AppException
from app.db.init_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await connect_db()
    await init_db(db)
    Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    yield
    await close_db()


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan, docs_url="/docs" if settings.DEBUG else None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exc_handler(_, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.message, "error_code": exc.error_code})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.APP_NAME}
