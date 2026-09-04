import asyncio
import logging

from app.core.database import connect_db, get_database
from app.services.tool_job_service import ToolJobService

logger = logging.getLogger(__name__)


async def run() -> None:
    await connect_db()
    db = get_database()
    logger.info("Tool worker started")
    while True:
        job = await db["jobs"].find_one_and_update(
            {"status": "pending", "type": "tool_process"},
            {"$set": {"status": "processing"}},
            sort=[("created_at", 1)],
        )
        if not job:
            await asyncio.sleep(1)
            continue
        try:
            await ToolJobService(db).process_job(job["job_id"])
            await db["jobs"].update_one({"_id": job["_id"]}, {"$set": {"status": "completed"}})
        except Exception as exc:
            logger.exception("Worker error")
            await db["jobs"].update_one({"_id": job["_id"]}, {"$set": {"status": "failed", "error": str(exc)}})


if __name__ == "__main__":
    asyncio.run(run())
