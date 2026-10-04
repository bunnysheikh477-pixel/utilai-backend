# from fastapi import APIRouter, Depends, File, Query, UploadFile, Request
# from fastapi.responses import FileResponse

# from app.api.deps import get_current_user_optional, get_super_admin
# from app.core.database import get_database
# from app.services.tool_job_service import ToolJobService
# from app.services.tool_service import ToolService
# from app.utils.file_validation import save_upload, validate_upload
# from app.utils.helpers import new_id

# router = APIRouter()


# @router.get("")
# async def list_tools(category: str | None = None, popular: bool = False):
#     db = get_database()
#     tools = await ToolService(db).list_published(category, popular)
#     return {"success": True, "data": tools}


# @router.get("/search")
# async def search_tools(q: str = Query(min_length=1)):
#     db = get_database()
#     results = await ToolService(db).search(q)
#     return {"success": True, "data": results}


# @router.get("/jobs/{job_id}")
# async def get_job(job_id: str):
#     db = get_database()
#     job = await ToolJobService(db).get_job(job_id)
#     if not job:
#         return {"success": False, "message": "Job not found"}
#     return {"success": True, "data": job}


# @router.get("/jobs/{job_id}/download")
# async def download_result(job_id: str):
#     db = get_database()
#     job = await ToolJobService(db).get_job(job_id)
#     if not job or job.get("status") != "completed":
#         return {"success": False, "message": "Result not ready"}
#     result = job.get("result", {})
#     path = result.get("output") or (result.get("outputs") or [None])[0]
#     if not path:
#         return {"success": False, "message": "No output file"}
#     return FileResponse(path, filename=path.split("/")[-1].split("\\")[-1])


# @router.get("/{category}/{slug}")
# async def get_tool(category: str, slug: str):
#     db = get_database()
#     tool = await ToolService(db).get_by_slug(category, slug)
#     if not tool:
#         return {"success": False, "message": "Tool not found", "error_code": "NOT_FOUND"}
#     await ToolService(db).track_view(slug)
#     return {"success": True, "data": tool}


# @router.post("/{category}/{slug}/process")
# async def process_tool(
#     category: str,
#     slug: str,
#     request: Request,
#     files: list[UploadFile] = File(...),
#     user=Depends(get_current_user_optional),
# ):
#     db = get_database()
#     tool = await ToolService(db).get_by_slug(category, slug)
#     if not tool:
#         return {"success": False, "message": "Tool not found"}
#     if tool["processing_type"] == "client":
#         return {"success": False, "message": "This tool runs client-side", "error_code": "CLIENT_SIDE_ONLY"}

#     session_id = new_id()
#     paths = []
#     allowed = tool.get("accepted_formats", [])
#     for f in files:
#         content = await f.read()
#         validate_upload(f.filename or "file", content, allowed)
#         paths.append(save_upload(content, f.filename or "file", session_id))

#     job = await ToolJobService(db).create_job(
#         slug, paths, {}, user_id=user.get("id") if user else None, ip=request.client.host if request.client else None
#     )
#     return {"success": True, "data": {"job_id": job["id"], "status": "pending"}}





from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

from app.api.deps import get_current_user_optional
from app.core.database import get_database
from app.services.tool_job_service import ToolJobService
from app.services.tool_service import ToolService
from app.utils.file_validation import save_upload, validate_upload
from app.utils.helpers import new_id


router = APIRouter()


# ============================================================
# LIST TOOLS
# ============================================================

@router.get("")
async def list_tools(
    category: str | None = None,
    popular: bool = False,
):

    db = get_database()

    tools = await ToolService(
        db
    ).list_published(
        category,
        popular,
    )

    return {
        "success": True,
        "data": tools,
    }


# ============================================================
# SEARCH TOOLS
# ============================================================

@router.get("/search")
async def search_tools(
    q: str = Query(min_length=1),
):

    db = get_database()

    results = await ToolService(
        db
    ).search(q)

    return {
        "success": True,
        "data": results,
    }


# ============================================================
# GET JOB
# ============================================================

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
):

    db = get_database()

    job = await ToolJobService(
        db
    ).get_job(job_id)

    if not job:

        return {
            "success": False,
            "message": "Job not found",
        }

    return {
        "success": True,
        "data": job,
    }


# ============================================================
# DOWNLOAD RESULT
# ============================================================

@router.get("/jobs/{job_id}/download")
async def download_result(
    job_id: str,
):

    db = get_database()

    job = await ToolJobService(
        db
    ).get_job(job_id)

    if not job:

        return {
            "success": False,
            "message": "Job not found",
        }

    if job.get("status") != "completed":

        return {
            "success": False,
            "message": "Result not ready",
        }

    result = job.get(
        "result",
        {},
    )

    path = (
        result.get("output")
        or (result.get("outputs") or [None])[0]
    )

    if not path:

        return {
            "success": False,
            "message": "No output file",
        }

    file_path = str(path)

    return FileResponse(
        file_path,
        filename=file_path.replace(
            "\\",
            "/",
        ).split("/")[-1],
    )


# ============================================================
# GET TOOL
# ============================================================

@router.get("/{category}/{slug}")
async def get_tool(
    category: str,
    slug: str,
):

    db = get_database()

    tool = await ToolService(
        db
    ).get_by_slug(
        category,
        slug,
    )

    if not tool:

        return {
            "success": False,
            "message": "Tool not found",
            "error_code": "NOT_FOUND",
        }

    await ToolService(
        db
    ).track_view(slug)

    return {
        "success": True,
        "data": tool,
    }


# ============================================================
# PROCESS TOOL
# ============================================================

@router.post("/{category}/{slug}/process")
async def process_tool(
    category: str,
    slug: str,
    request: Request,
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user_optional),
):

    db = get_database()

    # --------------------------------------------------------
    # FIND TOOL
    # --------------------------------------------------------

    tool = await ToolService(
        db
    ).get_by_slug(
        category,
        slug,
    )

    if not tool:

        return {
            "success": False,
            "message": "Tool not found",
        }

    # --------------------------------------------------------
    # CLIENT-SIDE TOOL CHECK
    # --------------------------------------------------------

    if tool["processing_type"] == "client":

        return {
            "success": False,
            "message": "This tool runs client-side",
            "error_code": "CLIENT_SIDE_ONLY",
        }

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    session_id = new_id()

    paths = []

    allowed = tool.get(
        "accepted_formats",
        [],
    )

    # --------------------------------------------------------
    # SAVE UPLOADS
    # --------------------------------------------------------

    for uploaded_file in files:

        filename = uploaded_file.filename or "file"

        content = await uploaded_file.read()

        validate_upload(
            filename,
            content,
            allowed,
        )

        saved_path = save_upload(
            content,
            filename,
            session_id,
        )

        paths.append(
            saved_path
        )

    # --------------------------------------------------------
    # CREATE JOB
    # --------------------------------------------------------

    job = await ToolJobService(
        db
    ).create_job(
        tool_slug=slug,
        file_paths=paths,
        options={},
        user_id=user.get("id") if user else None,
        ip=(
            request.client.host
            if request.client
            else None
        ),
    )

    return {
        "success": True,
        "data": {
            "job_id": job["id"],
            "status": "pending",
        },
    }