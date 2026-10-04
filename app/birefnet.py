# from __future__ import annotations

# import json
# import logging
# import os
# from pathlib import Path
# from urllib import error, request

# import torch
# from PIL import Image
# from torchvision import transforms
# from transformers import AutoModelForImageSegmentation

# from app.core.config import get_settings

# logger = logging.getLogger(__name__)

# _settings = get_settings()

# MODEL_NAME = (
#     os.getenv("BIREFNET_MODEL_NAME")
#     or _settings.BIREFNET_MODEL_NAME
#     or "ZhengPeng7/BiRefNet"
# )
# REMOTE_URL = (
#     os.getenv("BIREFNET_REMOTE_URL")
#     or _settings.BIREFNET_REMOTE_URL
#     or ""
# ).strip()
# REMOTE_MODE = (
#     os.getenv("BIREFNET_MODE")
#     or _settings.BIREFNET_MODE
#     or "local"
# ).strip().lower() == "remote"
# MEAN = [0.485, 0.456, 0.406]
# STD = [0.229, 0.224, 0.225]

# if torch.cuda.is_available():
#     torch.cuda.set_device(0)
#     torch.backends.cuda.matmul.allow_tf32 = True
#     torch.backends.cudnn.allow_tf32 = True

# DEVICE = torch.device(
#     "cuda" if torch.cuda.is_available() else "cpu"
# )
# IMAGE_SIZE = (512, 512) if DEVICE.type == "cpu" else (1024, 1024)

# transform = transforms.Compose(
#     [
#         transforms.Resize(IMAGE_SIZE),
#         transforms.ToTensor(),
#         transforms.Normalize(MEAN, STD),
#     ]
# )


# class BiRefNetService:

#     def __init__(self):
#         self.remote_url = REMOTE_URL
#         self.use_remote = REMOTE_MODE or bool(self.remote_url)

#         logger.info("=" * 60)
#         logger.info("Initializing BiRefNet")
#         logger.info("=" * 60)

#         if self.use_remote:
#             logger.info("Remote BiRefNet mode enabled.")
#             logger.info("Remote URL: %s", self.remote_url)
#             self.model = None
#             return

#         logger.info("CUDA available: %s", torch.cuda.is_available())
#         logger.info("Device: %s", DEVICE)
#         if torch.cuda.is_available():
#             logger.info("GPU: %s", torch.cuda.get_device_name(0))
#         logger.info("Model: %s", MODEL_NAME)

#         self.model = AutoModelForImageSegmentation.from_pretrained(
#             MODEL_NAME,
#             trust_remote_code=True,
#         )

#         self.model = self.model.to(DEVICE)
#         self.model.eval()

#         self.dtype = next(
#             self.model.parameters()
#         ).dtype

#         logger.info(
#             "Model dtype: %s",
#             self.dtype,
#         )

#         logger.info(
#             "BiRefNet loaded successfully."
#         )

#     def _remove_background_remote(
#         self,
#         input_path: str | Path,
#         output_path: str | Path,
#     ) -> dict:
#         if not self.remote_url:
#             raise RuntimeError(
#                 "BIREFNET_REMOTE_URL is not configured."
#             )

#         input_path = Path(input_path)
#         output_path = Path(output_path)

#         if not input_path.exists():
#             raise FileNotFoundError(
#                 f"Input file not found: {input_path}"
#             )

#         logger.info(
#             "Sending image to remote BiRefNet service: %s",
#             self.remote_url,
#         )

#         with input_path.open("rb") as file_obj:
#             file_bytes = file_obj.read()

#         boundary = "----BiRefNetBoundary"
#         body = (
#             b"--" + boundary.encode() + b"\r\n"
#             + b'Content-Disposition: form-data; name="file"; filename="' + input_path.name.encode() + b'"\r\n'
#             + b"Content-Type: image/png\r\n\r\n"
#             + file_bytes
#             + b"\r\n--" + boundary.encode() + b"--\r\n"
#         )

#         req = request.Request(
#             self.remote_url,
#             data=body,
#             headers={
#                 "Content-Type": f"multipart/form-data; boundary={boundary}",
#                 "Accept": "image/png, application/json",
#             },
#             method="POST",
#         )

#         try:
#             with request.urlopen(req, timeout=600) as response:
#                 content_type = response.headers.get_content_type()
#                 payload = response.read()
#         except error.HTTPError as exc:
#             try:
#                 detail = exc.read().decode("utf-8", errors="replace")
#             except Exception:
#                 detail = str(exc)
#             raise RuntimeError(
#                 f"Remote BiRefNet request failed: {detail}"
#             ) from exc

#         output_path.parent.mkdir(parents=True, exist_ok=True)

#         if content_type == "image/png":
#             output_path.write_bytes(payload)
#             logger.info("Saved remote result: %s", output_path)
#             return {
#                 "filename": output_path.name,
#                 "width": 0,
#                 "height": 0,
#                 "output_path": str(output_path),
#             }

#         try:
#             data = json.loads(payload.decode("utf-8"))
#         except Exception as exc:
#             raise RuntimeError(
#                 "Remote BiRefNet returned an unexpected response."
#             ) from exc

#         if isinstance(data, dict) and "image" in data:
#             image_bytes = data["image"]
#             if isinstance(image_bytes, str):
#                 output_path.write_bytes(
#                     image_bytes.encode("utf-8")
#                 )
#             else:
#                 output_path.write_bytes(image_bytes)
#             logger.info("Saved remote result: %s", output_path)
#             return {
#                 "filename": output_path.name,
#                 "width": 0,
#                 "height": 0,
#                 "output_path": str(output_path),
#             }

#         raise RuntimeError(
#             f"Remote BiRefNet response was not an image: {data}"
#         )

#     def remove_background(
#         self,
#         input_path: str | Path,
#         output_path: str | Path,
#     ) -> dict:
#         if self.use_remote:
#             return self._remove_background_remote(
#                 input_path,
#                 output_path,
#             )

#         input_path = Path(input_path)
#         output_path = Path(output_path)

#         if not input_path.exists():
#             raise FileNotFoundError(
#                 f"Input file not found: {input_path}"
#             )

#         logger.info(
#             "Processing: %s",
#             input_path,
#         )

#         image = Image.open(
#             input_path
#         ).convert("RGB")

#         original_size = image.size

#         tensor = transform(image)
#         tensor = tensor.unsqueeze(0)
#         tensor = tensor.to(
#             device=DEVICE,
#             dtype=self.dtype,
#         )

#         with torch.inference_mode():
#             prediction = self.model(
#                 tensor
#             )

#             if isinstance(
#                 prediction,
#                 (tuple, list),
#             ):
#                 prediction = prediction[-1]

#             elif hasattr(
#                 prediction,
#                 "logits",
#             ):
#                 prediction = prediction.logits

#         prediction = prediction.float()
#         prediction = prediction.sigmoid()
#         prediction = prediction.squeeze()

#         mask = transforms.ToPILImage()(
#             prediction.cpu()
#         )

#         mask = mask.resize(
#             original_size,
#             Image.Resampling.LANCZOS,
#         )

#         result = image.convert("RGBA")
#         result.putalpha(mask)

#         output_path.parent.mkdir(
#             parents=True,
#             exist_ok=True,
#         )

#         result.save(
#             output_path,
#             format="PNG",
#         )

#         logger.info(
#             "Saved result: %s",
#             output_path,
#         )

#         return {
#             "filename": output_path.name,
#             "width": original_size[0],
#             "height": original_size[1],
#             "output_path": str(output_path),
#         }


# birefnet_service = BiRefNetService()





from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from urllib import error, request

import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

from app.core.config import get_settings


logger = logging.getLogger(__name__)

_settings = get_settings()


# ============================================================
# Environment / Model Configuration
# ============================================================

MODEL_NAME = (
    os.getenv("BIREFNET_MODEL_NAME")
    or _settings.BIREFNET_MODEL_NAME
    or "ZhengPeng7/BiRefNet"
)

REMOTE_URL = (
    os.getenv("BIREFNET_REMOTE_URL")
    or _settings.BIREFNET_REMOTE_URL
    or ""
).strip()

REMOTE_MODE = (
    os.getenv("BIREFNET_MODE")
    or _settings.BIREFNET_MODE
    or "local"
).strip().lower() == "remote"


# Hugging Face token
#
# IMPORTANT:
# Do NOT put the real token directly in this file.
# Railway should provide it through:
#
# HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
#
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()


# Optional model revision.
#
# You can leave this empty for now.
# Later you can set a specific Hugging Face commit/revision
# for better reproducibility and security.
BIREFNET_REVISION = os.getenv(
    "BIREFNET_REVISION",
    "",
).strip()


MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


# ============================================================
# Device Configuration
# ============================================================

if torch.cuda.is_available():
    torch.cuda.set_device(0)

    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# CPU -> smaller image to reduce RAM usage
# GPU -> larger image for better quality
IMAGE_SIZE = (
    (1024, 1024)
    if DEVICE.type == "cuda"
    else (512, 512)
)


# ============================================================
# Image Transform
# ============================================================

transform = transforms.Compose(
    [
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ]
)


# ============================================================
# BiRefNet Service
# ============================================================

class BiRefNetService:

    def __init__(self):
        self.remote_url = REMOTE_URL
        self.use_remote = (
            REMOTE_MODE
            or bool(self.remote_url)
        )

        logger.info("=" * 60)
        logger.info("Initializing BiRefNet")
        logger.info("=" * 60)

        # ----------------------------------------------------
        # Remote mode
        # ----------------------------------------------------

        if self.use_remote:
            logger.info(
                "Remote BiRefNet mode enabled."
            )

            logger.info(
                "Remote URL: %s",
                self.remote_url,
            )

            self.model = None
            self.dtype = torch.float32

            return

        # ----------------------------------------------------
        # Local model mode
        # ----------------------------------------------------

        logger.info(
            "CUDA available: %s",
            torch.cuda.is_available(),
        )

        logger.info(
            "Device: %s",
            DEVICE,
        )

        if torch.cuda.is_available():
            logger.info(
                "GPU: %s",
                torch.cuda.get_device_name(0),
            )

        logger.info(
            "Model: %s",
            MODEL_NAME,
        )

        # ----------------------------------------------------
        # Hugging Face authentication
        # ----------------------------------------------------

        if HF_TOKEN:
            logger.info(
                "Hugging Face token detected."
            )
        else:
            logger.warning(
                "HF_TOKEN is not configured. "
                "Hugging Face requests will be unauthenticated."
            )

        # ----------------------------------------------------
        # Model loading arguments
        # ----------------------------------------------------

        model_kwargs = {
            "trust_remote_code": True,
        }

        # Only send token when it exists.
        #
        # This prevents passing an empty token to
        # transformers/Hugging Face.
        if HF_TOKEN:
            model_kwargs["token"] = HF_TOKEN

        # Optional revision pinning.
        #
        # Example:
        # BIREFNET_REVISION=<commit-hash>
        #
        # We intentionally do not hardcode a fake revision.
        if BIREFNET_REVISION:
            model_kwargs["revision"] = BIREFNET_REVISION

            logger.info(
                "BiRefNet revision: %s",
                BIREFNET_REVISION,
            )

        # ----------------------------------------------------
        # Download / load BiRefNet
        # ----------------------------------------------------

        logger.info(
            "Loading BiRefNet from Hugging Face..."
        )

        self.model = (
            AutoModelForImageSegmentation.from_pretrained(
                MODEL_NAME,
                **model_kwargs,
            )
        )

        # ----------------------------------------------------
        # Move model to CPU/GPU
        # ----------------------------------------------------

        self.model = self.model.to(DEVICE)

        self.model.eval()

        # ----------------------------------------------------
        # Detect model dtype
        # ----------------------------------------------------

        self.dtype = next(
            self.model.parameters()
        ).dtype

        logger.info(
            "Model dtype: %s",
            self.dtype,
        )

        logger.info(
            "BiRefNet loaded successfully."
        )

        logger.info("=" * 60)


    # ========================================================
    # Remote BiRefNet
    # ========================================================

    def _remove_background_remote(
        self,
        input_path: str | Path,
        output_path: str | Path,
    ) -> dict:

        if not self.remote_url:
            raise RuntimeError(
                "BIREFNET_REMOTE_URL is not configured."
            )

        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        logger.info(
            "Sending image to remote BiRefNet service: %s",
            self.remote_url,
        )

        with input_path.open("rb") as file_obj:
            file_bytes = file_obj.read()

        boundary = "----BiRefNetBoundary"

        body = (
            b"--"
            + boundary.encode()
            + b"\r\n"
            + b'Content-Disposition: form-data; '
              b'name="file"; filename="'
            + input_path.name.encode()
            + b'"\r\n'
            + b"Content-Type: image/png\r\n\r\n"
            + file_bytes
            + b"\r\n--"
            + boundary.encode()
            + b"--\r\n"
        )

        req = request.Request(
            self.remote_url,
            data=body,
            headers={
                "Content-Type": (
                    "multipart/form-data; "
                    f"boundary={boundary}"
                ),
                "Accept": (
                    "image/png, application/json"
                ),
            },
            method="POST",
        )

        try:
            with request.urlopen(
                req,
                timeout=600,
            ) as response:

                content_type = (
                    response.headers.get_content_type()
                )

                payload = response.read()

        except error.HTTPError as exc:

            try:
                detail = exc.read().decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                detail = str(exc)

            raise RuntimeError(
                "Remote BiRefNet request failed: "
                f"{detail}"
            ) from exc

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # PNG response
        # ----------------------------------------------------

        if content_type == "image/png":

            output_path.write_bytes(
                payload
            )

            logger.info(
                "Saved remote result: %s",
                output_path,
            )

            return {
                "filename": output_path.name,
                "width": 0,
                "height": 0,
                "output_path": str(output_path),
            }

        # ----------------------------------------------------
        # JSON response
        # ----------------------------------------------------

        try:
            data = json.loads(
                payload.decode("utf-8")
            )

        except Exception as exc:

            raise RuntimeError(
                "Remote BiRefNet returned "
                "an unexpected response."
            ) from exc

        if (
            isinstance(data, dict)
            and "image" in data
        ):

            image_bytes = data["image"]

            if isinstance(
                image_bytes,
                str,
            ):
                output_path.write_bytes(
                    image_bytes.encode("utf-8")
                )
            else:
                output_path.write_bytes(
                    image_bytes
                )

            logger.info(
                "Saved remote result: %s",
                output_path,
            )

            return {
                "filename": output_path.name,
                "width": 0,
                "height": 0,
                "output_path": str(output_path),
            }

        raise RuntimeError(
            "Remote BiRefNet response was not "
            f"an image: {data}"
        )


    # ========================================================
    # Main Background Removal
    # ========================================================

    def remove_background(
        self,
        input_path: str | Path,
        output_path: str | Path,
    ) -> dict:

        # ----------------------------------------------------
        # Remote mode
        # ----------------------------------------------------

        if self.use_remote:

            return self._remove_background_remote(
                input_path,
                output_path,
            )

        # ----------------------------------------------------
        # Local mode
        # ----------------------------------------------------

        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        logger.info(
            "Processing: %s",
            input_path,
        )

        # ----------------------------------------------------
        # Load image
        # ----------------------------------------------------

        image = Image.open(
            input_path
        ).convert("RGB")

        original_size = image.size

        # ----------------------------------------------------
        # Transform image
        # ----------------------------------------------------

        tensor = transform(image)

        tensor = tensor.unsqueeze(0)

        tensor = tensor.to(
            device=DEVICE,
            dtype=self.dtype,
        )

        # ----------------------------------------------------
        # Model inference
        # ----------------------------------------------------

        with torch.inference_mode():

            prediction = self.model(
                tensor
            )

            if isinstance(
                prediction,
                (tuple, list),
            ):
                prediction = prediction[-1]

            elif hasattr(
                prediction,
                "logits",
            ):
                prediction = (
                    prediction.logits
                )

        # ----------------------------------------------------
        # Convert prediction to mask
        # ----------------------------------------------------

        prediction = prediction.float()

        prediction = prediction.sigmoid()

        prediction = prediction.squeeze()

        mask = transforms.ToPILImage()(
            prediction.cpu()
        )

        # ----------------------------------------------------
        # Restore original image size
        # ----------------------------------------------------

        mask = mask.resize(
            original_size,
            Image.Resampling.LANCZOS,
        )

        # ----------------------------------------------------
        # Apply alpha mask
        # ----------------------------------------------------

        result = image.convert(
            "RGBA"
        )

        result.putalpha(
            mask
        )

        # ----------------------------------------------------
        # Save output
        # ----------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        result.save(
            output_path,
            format="PNG",
        )

        logger.info(
            "Saved result: %s",
            output_path,
        )

        return {
            "filename": output_path.name,
            "width": original_size[0],
            "height": original_size[1],
            "output_path": str(output_path),
        }


# ============================================================
# Global BiRefNet Service
# ============================================================

birefnet_service = BiRefNetService()

