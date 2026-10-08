from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
from PIL import Image

from app.core.config import get_settings


logger = logging.getLogger(__name__)
_settings = get_settings()

REMOVE_BG_URL = "https://api.remove.bg/v1.0/removebg"
REMOVE_BG_API_KEY = (
    os.getenv("REMOVE_BG_API_KEY")
    or getattr(_settings, "REMOVE_BG_API_KEY", None)
    or ""
).strip()
REMOVE_BG_TIMEOUT = int(os.getenv("REMOVE_BG_TIMEOUT", "300"))


class BiRefNetService:
    def __init__(self) -> None:
        self.api_url = REMOVE_BG_URL
        self.api_key = REMOVE_BG_API_KEY

        if not self.api_key:
            logger.warning(
                "REMOVE_BG_API_KEY is not configured. "
                "Background removal requests will fail until "
                "the API key is configured."
            )
        else:
            logger.info("remove.bg background removal service initialized.")

    def remove_background(
        self,
        input_path: str | Path,
        output_path: str | Path,
    ) -> dict:
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not self.api_key:
            raise RuntimeError(
                "REMOVE_BG_API_KEY is not configured. "
                "Please add your remove.bg API key."
            )

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            with Image.open(input_path) as image:
                width, height = image.size
                image_format = image.format
        except Exception as exc:
            raise RuntimeError(
                f"Could not open input image: {input_path}"
            ) from exc

        logger.info(
            "Sending image to remove.bg | format=%s | size=%sx%s",
            image_format,
            width,
            height,
        )

        try:
            with input_path.open("rb") as image_file:
                response = requests.post(
                    self.api_url,
                    headers={"X-Api-Key": self.api_key},
                    files={"image_file": (input_path.name, image_file)},
                    data={"size": "auto"},
                    timeout=REMOVE_BG_TIMEOUT,
                )
        except requests.Timeout as exc:
            raise RuntimeError("remove.bg API request timed out.") from exc
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not connect to remove.bg API: {exc}"
            ) from exc

        if not response.ok:
            try:
                error_data = response.json()
                errors = error_data.get("errors")
                error_message = str(errors if errors else error_data)
            except Exception:
                error_message = response.text

            raise RuntimeError(
                f"remove.bg API request failed "
                f"(HTTP {response.status_code}): {error_message}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            output_path.write_bytes(response.content)
            with Image.open(output_path) as result:
                result_width, result_height = result.size
                result_format = result.format
                result_mode = result.mode
        except Exception as exc:
            raise RuntimeError(
                "remove.bg returned an invalid image or it could not be saved."
            ) from exc

        logger.info(
            "Background removed | format=%s | mode=%s | size=%sx%s | output=%s",
            result_format,
            result_mode,
            result_width,
            result_height,
            output_path,
        )
        return {
            "filename": output_path.name,
            "width": result_width,
            "height": result_height,
            "output_path": str(output_path),
        }


birefnet_service = BiRefNetService()
