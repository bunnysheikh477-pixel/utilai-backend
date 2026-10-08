
from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
import shutil
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.v1.router import api_router
from app.birefnet import birefnet_service
from app.core.config import get_settings
from app.core.database import (
    close_db,
    connect_db,
    is_using_memory_db,
)
from app.core.exceptions import AppException
from app.db.init_db import init_db


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

INPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SETTINGS
# ============================================================

settings = get_settings()


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    database = await connect_db()

    try:
        await init_db(database)

        Path(settings.STORAGE_DIR).mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info("========================================")
        logger.info("Application startup complete")
        logger.info(
            "Database mode: %s",
            "memory" if is_using_memory_db() else "mongodb",
        )

        # logger.info(
        #     "BiRefNet mode: %s",
        #     (
        #         "remote"
        #         if birefnet_service.use_remote
        #         else str(DEVICE)
        #     ),
        # )
        logger.info(
          "Background remover: remove.bg API"
        )
        logger.info("========================================")

        yield

    finally:
        await close_db()

        logger.info(
            "Database connection closed."
        )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTER
# ============================================================

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


# ============================================================
# APPLICATION EXCEPTION HANDLER
# ============================================================

@app.exception_handler(AppException)
async def app_exception_handler(
    _,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
        },
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "success": True,
        "status": "healthy",
        "service": settings.APP_NAME,
        "database": (
            "memory"
            if is_using_memory_db()
            else "mongodb"
        ),
        "device": "remove.bg",
        "hf_token_configured": bool(
            os.getenv("HF_TOKEN")
        ),
    }


# ============================================================
# BACKGROUND REMOVER
# ============================================================

@app.post("/remove-background")
def remove_background(
    file: UploadFile = File(...),
):
    # --------------------------------------------------------
    # VALIDATE FILE
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use JPG, JPEG, PNG or WebP."
            ),
        )

    # --------------------------------------------------------
    # CREATE UNIQUE JOB ID
    # --------------------------------------------------------

    job_id = uuid.uuid4().hex

    input_path = (
        INPUT_DIR
        / f"{job_id}{extension}"
    )

    output_path = (
        OUTPUT_DIR
        / f"{job_id}.png"
    )

    try:
        # ----------------------------------------------------
        # SAVE UPLOADED FILE
        # ----------------------------------------------------

        with input_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        logger.info(
            "Uploaded image: %s",
            input_path,
        )

        # ----------------------------------------------------
        # PROCESS IMAGE
        # ----------------------------------------------------

        birefnet_service.remove_background(
            input_path,
            output_path,
        )

        # ----------------------------------------------------
        # CHECK OUTPUT
        # ----------------------------------------------------

        if not output_path.exists():
            raise RuntimeError(
                "Background removal completed "
                "but output file was not created."
            )

        logger.info(
            "Background removal completed: %s",
            output_path,
        )

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return FileResponse(
            path=str(output_path),
            media_type="image/png",
            filename="background_removed.png",
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Background removal failed.",
        )

        if output_path.exists():
            output_path.unlink(
                missing_ok=True,
            )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:
        # ----------------------------------------------------
        # REMOVE ORIGINAL UPLOAD
        # ----------------------------------------------------

        if input_path.exists():
            input_path.unlink(
                missing_ok=True,
            )


# ============================================================
# GET RESULT
# ============================================================

@app.get("/result/{job_id}")
async def get_result(
    job_id: str,
):
    output_path = (
        OUTPUT_DIR
        / f"{job_id}.png"
    )

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Result not found.",
        )

    return FileResponse(
        path=str(output_path),
        media_type="image/png",
        filename="background_removed.png",
    )


# ============================================================
# SERVER ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Railway provides PORT automatically.
    # Local development uses port 8001.

    port = int(
        os.environ.get(
            "PORT",
            "8001",
        )
    )

    logger.info(
        "Starting server on 0.0.0.0:%s",
        port,
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
