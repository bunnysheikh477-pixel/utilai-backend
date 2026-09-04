from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import AppException


def validate_upload(filename: str, content: bytes, allowed_exts: list[str], max_mb: Optional[int] = None) -> str:
    settings = get_settings()
    max_bytes = (max_mb or settings.MAX_UPLOAD_MB_FREE) * 1024 * 1024
    if len(content) > max_bytes:
        raise AppException(
            f"File exceeds maximum size of {max_mb or settings.MAX_UPLOAD_MB_FREE}MB",
            "FILE_TOO_LARGE",
            413,
        )
    ext = Path(filename).suffix.lower().lstrip(".")
    if allowed_exts and ext not in allowed_exts:
        raise AppException(f"Unsupported file type: .{ext}", "UNSUPPORTED_FORMAT", 400)
    # Basic magic-byte checks
    if ext == "pdf" and not content[:4] == b"%PDF":
        raise AppException("Invalid PDF file", "INVALID_FILE", 400)
    if ext in ("jpg", "jpeg") and not content[:3] == b"\xff\xd8\xff":
        raise AppException("Invalid JPEG file", "INVALID_FILE", 400)
    if ext == "png" and not content[:8] == b"\x89PNG\r\n\x1a\n":
        raise AppException("Invalid PNG file", "INVALID_FILE", 400)
    return ext


def save_upload(content: bytes, filename: str, session_id: str) -> str:
    from app.utils.helpers import new_id

    settings = get_settings()
    storage = Path(settings.STORAGE_DIR) / "uploads" / session_id
    storage.mkdir(parents=True, exist_ok=True)
    safe_name = f"{new_id()}{Path(filename).suffix.lower()}"
    path = storage / safe_name
    path.write_bytes(content)
    return str(path)
