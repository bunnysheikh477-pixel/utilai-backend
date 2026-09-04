import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.enums import JobStatus
from app.tools.registry import get_processor
from app.utils.helpers import new_id, serialize, utcnow

logger = logging.getLogger(__name__)


class ToolJobService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.settings = get_settings()

    async def create_job(
        self,
        tool_slug: str,
        file_paths: list[str],
        options: dict[str, Any],
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> dict[str, Any]:
        tool = await self.db["tools"].find_one({"slug": tool_slug, "status": "published"})
        if not tool:
            raise AppException("Tool not found", "TOOL_NOT_FOUND", 404)

        job_id = new_id()
        doc = {
            "_id": job_id,
            "tool_slug": tool_slug,
            "tool_id": tool["_id"],
            "status": JobStatus.PENDING.value,
            "file_paths": file_paths,
            "options": options,
            "user_id": user_id,
            "ip": ip,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        await self.db["tool_jobs"].insert_one(doc)
        await self.db["jobs"].insert_one({"_id": job_id, "type": "tool_process", "status": "pending", "created_at": utcnow(), "job_id": job_id})
        return serialize(doc)  # type: ignore

    async def process_job(self, job_id: str) -> None:
        job = await self.db["tool_jobs"].find_one({"_id": job_id})
        if not job:
            return
        await self.db["tool_jobs"].update_one({"_id": job_id}, {"$set": {"status": JobStatus.PROCESSING.value}})
        slug = job["tool_slug"]
        processor = get_processor(slug)
        if not processor:
            await self._fail(job_id, f"No processor for {slug}")
            return
        try:
            storage = Path(self.settings.STORAGE_DIR) / "results" / job_id
            storage.mkdir(parents=True, exist_ok=True)
            paths = job["file_paths"]
            opts = job.get("options", {})

            if slug == "merge-pdf":
                out = str(storage / "merged.pdf")
                result = processor(paths, out)
            elif slug == "split-pdf":
                outputs = processor(paths[0], str(storage))
                result = {"outputs": outputs}
            elif slug == "compress-pdf":
                out = str(storage / "compressed.pdf")
                result = processor(paths[0], out)
            elif slug == "pdf-to-jpg":
                outputs = processor(paths[0], str(storage))
                result = {"outputs": outputs}
            elif slug == "jpg-to-pdf":
                out = str(storage / "output.pdf")
                result = processor(paths, out)
            elif slug == "compress-image":
                out = str(storage / "compressed.jpg")
                result = processor(paths[0], out, opts.get("quality", 80))
            else:
                raise ValueError(f"Unhandled tool: {slug}")

            await self.db["tool_jobs"].update_one(
                {"_id": job_id},
                {"$set": {"status": JobStatus.COMPLETED.value, "result": result, "updated_at": utcnow()}},
            )
            await self._track_usage(job)
        except Exception as exc:
            logger.exception("Job %s failed", job_id)
            await self._fail(job_id, str(exc))

    async def _fail(self, job_id: str, error: str) -> None:
        await self.db["tool_jobs"].update_one(
            {"_id": job_id},
            {"$set": {"status": JobStatus.FAILED.value, "error": error, "updated_at": utcnow()}},
        )

    async def _track_usage(self, job: dict) -> None:
        await self.db["tool_usage"].insert_one({
            "_id": new_id(),
            "tool_id": job["tool_id"],
            "tool_slug": job["tool_slug"],
            "user_id": job.get("user_id"),
            "ip": job.get("ip"),
            "status": "completed",
            "created_at": utcnow(),
        })
        await self.db["analytics_events"].insert_one({
            "_id": new_id(),
            "event_type": "tool_complete",
            "tool_slug": job["tool_slug"],
            "created_at": utcnow(),
        })

    async def get_job(self, job_id: str) -> Optional[dict]:
        return serialize(await self.db["tool_jobs"].find_one({"_id": job_id}))
