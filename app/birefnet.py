


# from __future__ import annotations

# import base64
# import binascii
# import gc
# import json
# import logging
# import os
# import threading
# from pathlib import Path
# from urllib import error, request

# import torch
# from PIL import Image
# from torchvision import transforms
# from transformers import AutoModelForImageSegmentation

# from app.core.config import get_settings


# logger = logging.getLogger(__name__)

# _settings = get_settings()


# # ============================================================
# # Device
# # ============================================================

# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# if DEVICE.type == "cuda":
#     try:
#         torch.cuda.set_device(0)
#         torch.backends.cuda.matmul.allow_tf32 = True
#         torch.backends.cudnn.allow_tf32 = True
#     except Exception as exc:
#         logger.warning("Could not configure CUDA optimizations: %s", exc)
# else:
#     # Railway containers share CPUs; fewer threads = lower RAM/CPU spikes.
#     try:
#         torch.set_num_threads(int(os.getenv("BIREFNET_THREADS", "2")))
#     except Exception:
#         pass


# # ============================================================
# # Configuration (all overridable from Railway variables)
# # ============================================================

# FULL_MODEL = "ZhengPeng7/BiRefNet"
# LITE_MODEL = "ZhengPeng7/BiRefNet_lite"

# # On CPU the lite model is used unless you explicitly set a model name.
# MODEL_NAME = (
#     os.getenv("BIREFNET_MODEL_NAME")
#     or getattr(_settings, "BIREFNET_MODEL_NAME", None)
#     or (FULL_MODEL if DEVICE.type == "cuda" else LITE_MODEL)
# ).strip()

# REMOTE_URL = (
#     os.getenv("BIREFNET_REMOTE_URL")
#     or getattr(_settings, "BIREFNET_REMOTE_URL", None)
#     or ""
# ).strip()

# REMOTE_MODE = (
#     os.getenv("BIREFNET_MODE")
#     or getattr(_settings, "BIREFNET_MODE", None)
#     or "local"
# ).strip().lower() == "remote"

# HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# # The pinned commit below belongs ONLY to the full BiRefNet repo.
# # For any other model (e.g. BiRefNet_lite) no revision is sent unless
# # you set BIREFNET_REVISION yourself, otherwise HF returns "revision not found".
# DEFAULT_BIREFNET_REVISION = "e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4"

# BIREFNET_REVISION = (
#     os.getenv("BIREFNET_REVISION")
#     or (DEFAULT_BIREFNET_REVISION if MODEL_NAME == FULL_MODEL else "")
# ).strip()

# # false (default): model loads on first request, so the app always starts
# # and passes the healthcheck. true: load at startup.
# PRELOAD = os.getenv("BIREFNET_PRELOAD", "false").strip().lower() == "true"

# # CPU only: bfloat16 roughly halves model RAM. Default stays float32.
# CPU_DTYPE_NAME = os.getenv("BIREFNET_DTYPE", "float32").strip().lower()

# MEAN = [0.485, 0.456, 0.406]
# STD = [0.229, 0.224, 0.225]

# _default_size = 1024 if DEVICE.type == "cuda" else 512
# _size = int(os.getenv("BIREFNET_IMAGE_SIZE", str(_default_size)))
# IMAGE_SIZE = (_size, _size)

# transform = transforms.Compose(
#     [
#         transforms.Resize(
#             IMAGE_SIZE,
#             interpolation=transforms.InterpolationMode.BILINEAR,
#         ),
#         transforms.ToTensor(),
#         transforms.Normalize(MEAN, STD),
#     ]
# )


# # ============================================================
# # Helpers
# # ============================================================

# def _extract_prediction(prediction):
#     """Get the segmentation tensor from different output formats."""
#     if isinstance(prediction, (tuple, list)):
#         if not prediction:
#             raise RuntimeError("BiRefNet returned an empty prediction.")
#         return prediction[-1]

#     if hasattr(prediction, "logits"):
#         return prediction.logits

#     return prediction


# # ============================================================
# # Service
# # ============================================================

# class BiRefNetService:

#     def __init__(self):
#         self.remote_url = REMOTE_URL
#         self.use_remote = REMOTE_MODE or bool(self.remote_url)

#         self.model = None
#         self.dtype = torch.float32

#         self._load_lock = threading.Lock()
#         self._infer_lock = threading.Lock()  # one inference at a time = no RAM spikes

#         logger.info("Initializing BiRefNet service")

#         if self.use_remote:
#             if not self.remote_url:
#                 raise RuntimeError(
#                     "BiRefNet remote mode is enabled, "
#                     "but BIREFNET_REMOTE_URL is not configured."
#                 )
#             logger.info("Remote mode enabled: %s", self.remote_url)
#             logger.info("Local BiRefNet model will NOT be loaded.")
#             return

#         logger.info(
#             "Local mode | device=%s | model=%s | revision=%s | preload=%s",
#             DEVICE,
#             MODEL_NAME,
#             BIREFNET_REVISION or "default",
#             PRELOAD,
#         )

#         if PRELOAD:
#             self.load_model()
#         else:
#             logger.info("Model will be loaded lazily on first request.")

#     # --------------------------------------------------------
#     # Model loading
#     # --------------------------------------------------------

#     def load_model(self) -> None:
#         """Load the model once (thread-safe)."""
#         if self.model is not None:
#             return

#         with self._load_lock:
#             if self.model is not None:
#                 return

#             if DEVICE.type == "cuda":
#                 try:
#                     logger.info("GPU: %s", torch.cuda.get_device_name(0))
#                 except Exception as exc:
#                     logger.warning("Could not read GPU information: %s", exc)

#             # NOTE: do not pass low_cpu_mem_usage=True here. BiRefNet's custom
#             # code builds tensors in __init__ and breaks with meta-device init.
#             model_kwargs = {"trust_remote_code": True}

#             if BIREFNET_REVISION:
#                 model_kwargs["revision"] = BIREFNET_REVISION

#             if HF_TOKEN:
#                 model_kwargs["token"] = HF_TOKEN
#             else:
#                 logger.warning(
#                     "HF_TOKEN is not configured. Requests will be unauthenticated."
#                 )

#             logger.info("Loading BiRefNet from Hugging Face...")

#             try:
#                 model = AutoModelForImageSegmentation.from_pretrained(
#                     MODEL_NAME,
#                     **model_kwargs,
#                 )
#             except Exception:
#                 logger.exception("Failed to load BiRefNet model.")
#                 raise

#             model.eval()

#             for param in model.parameters():
#                 param.requires_grad_(False)

#             if DEVICE.type == "cpu" and CPU_DTYPE_NAME == "bfloat16":
#                 model = model.to(dtype=torch.bfloat16)

#             try:
#                 model = model.to(DEVICE)
#             except Exception:
#                 logger.exception("Failed to move BiRefNet to device: %s", DEVICE)
#                 raise

#             try:
#                 self.dtype = next(model.parameters()).dtype
#             except StopIteration:
#                 self.dtype = torch.float32

#             self.model = model
#             gc.collect()

#             logger.info(
#                 "BiRefNet loaded successfully | device=%s | dtype=%s",
#                 DEVICE,
#                 self.dtype,
#             )

#     # --------------------------------------------------------
#     # Remote
#     # --------------------------------------------------------

#     def _remove_background_remote(
#         self,
#         input_path: Path,
#         output_path: Path,
#     ) -> dict:

#         logger.info("Sending image to remote BiRefNet: %s", self.remote_url)

#         file_bytes = input_path.read_bytes()

#         boundary = "----BiRefNetBoundary"

#         body = (
#             b"--" + boundary.encode() + b"\r\n"
#             + b'Content-Disposition: form-data; name="file"; filename="'
#             + input_path.name.encode()
#             + b'"\r\n'
#             + b"Content-Type: application/octet-stream\r\n\r\n"
#             + file_bytes
#             + b"\r\n--" + boundary.encode() + b"--\r\n"
#         )

#         headers = {
#             "Content-Type": f"multipart/form-data; boundary={boundary}",
#             "Accept": "image/png, application/json",
#             # Lets ngrok free tunnels skip the browser warning page.
#             "ngrok-skip-browser-warning": "true",
#         }

#         req = request.Request(
#             self.remote_url,
#             data=body,
#             headers=headers,
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
#             raise RuntimeError(f"Remote BiRefNet request failed: {detail}") from exc

#         except error.URLError as exc:
#             raise RuntimeError(
#                 f"Could not connect to remote BiRefNet service: {exc}"
#             ) from exc

#         except TimeoutError as exc:
#             raise RuntimeError("Remote BiRefNet request timed out.") from exc

#         output_path.parent.mkdir(parents=True, exist_ok=True)

#         # Direct image response
#         if content_type.startswith("image/"):
#             output_path.write_bytes(payload)

#         # JSON response
#         else:
#             try:
#                 data = json.loads(payload.decode("utf-8"))
#             except Exception as exc:
#                 raise RuntimeError(
#                     "Remote BiRefNet returned an unexpected non-JSON response."
#                 ) from exc

#             if not isinstance(data, dict) or "image" not in data:
#                 raise RuntimeError(
#                     f"Remote BiRefNet response was not an image: {data}"
#                 )

#             image_data = data["image"]

#             if isinstance(image_data, str):
#                 encoded = image_data

#                 # data:image/png;base64,XXXX
#                 if "," in encoded:
#                     prefix, possible = encoded.split(",", 1)
#                     if "base64" in prefix.lower():
#                         encoded = possible

#                 try:
#                     output_path.write_bytes(base64.b64decode(encoded, validate=True))
#                 except (ValueError, binascii.Error) as exc:
#                     raise RuntimeError(
#                         "Remote BiRefNet returned invalid base64 image data."
#                     ) from exc

#             elif isinstance(image_data, (bytes, bytearray)):
#                 output_path.write_bytes(bytes(image_data))

#             else:
#                 raise RuntimeError(
#                     "Remote BiRefNet returned an unsupported 'image' value."
#                 )

#         width = height = 0
#         try:
#             with Image.open(output_path) as img:
#                 width, height = img.size
#         except Exception:
#             logger.warning("Remote result could not be read as an image.")

#         logger.info("Saved remote result: %s", output_path)

#         return {
#             "filename": output_path.name,
#             "width": width,
#             "height": height,
#             "output_path": str(output_path),
#         }

#     # --------------------------------------------------------
#     # Local
#     # --------------------------------------------------------

#     def _remove_background_local(
#         self,
#         input_path: Path,
#         output_path: Path,
#     ) -> dict:

#         self.load_model()

#         if self.model is None:
#             raise RuntimeError("BiRefNet model is not loaded.")

#         logger.info("Processing image: %s", input_path)

#         try:
#             image = Image.open(input_path).convert("RGB")
#         except Exception as exc:
#             raise RuntimeError(f"Could not open image: {input_path}") from exc

#         original_size = image.size

#         tensor = transform(image).unsqueeze(0).to(device=DEVICE, dtype=self.dtype)

#         try:
#             with self._infer_lock:
#                 with torch.inference_mode():
#                     prediction = self.model(tensor)
#         except Exception:
#             logger.exception("BiRefNet inference failed.")
#             raise

#         prediction = _extract_prediction(prediction)

#         if not isinstance(prediction, torch.Tensor):
#             raise RuntimeError(
#                 f"BiRefNet returned an unsupported prediction type: {type(prediction)}"
#             )

#         prediction = prediction.float().sigmoid().squeeze()

#         if prediction.ndim != 2:
#             raise RuntimeError(
#                 f"Unexpected BiRefNet mask shape: {tuple(prediction.shape)}"
#             )

#         mask = transforms.ToPILImage()(prediction.cpu())
#         mask = mask.resize(original_size, Image.Resampling.LANCZOS)

#         result = image.convert("RGBA")
#         result.putalpha(mask)

#         output_path.parent.mkdir(parents=True, exist_ok=True)
#         result.save(output_path, format="PNG")

#         logger.info("Saved background-removed image: %s", output_path)

#         # Free temporary memory
#         del tensor, prediction, mask, result, image
#         gc.collect()

#         if DEVICE.type == "cuda":
#             try:
#                 torch.cuda.empty_cache()
#             except Exception:
#                 pass

#         return {
#             "filename": output_path.name,
#             "width": original_size[0],
#             "height": original_size[1],
#             "output_path": str(output_path),
#         }

#     # --------------------------------------------------------
#     # Public API
#     # --------------------------------------------------------

#     def remove_background(
#         self,
#         input_path: str | Path,
#         output_path: str | Path,
#     ) -> dict:

#         input_path = Path(input_path)
#         output_path = Path(output_path)

#         if not input_path.exists():
#             raise FileNotFoundError(f"Input file not found: {input_path}")

#         if self.use_remote:
#             return self._remove_background_remote(input_path, output_path)

#         return self._remove_background_local(input_path, output_path)


# # ============================================================
# # Global instance
# # ============================================================
# # Creating it no longer loads the model (unless BIREFNET_PRELOAD=true),
# # so importing this module cannot crash the container anymore.

# birefnet_service = BiRefNetService()








from __future__ import annotations

import gc
import logging
import os
from pathlib import Path

import requests
from PIL import Image

from app.core.config import get_settings


logger = logging.getLogger(__name__)

_settings = get_settings()


# ============================================================
# Configuration
# ============================================================

REMOVE_BG_URL = "https://api.remove.bg/v1.0/removebg"

# Environment variable ko priority di gayi hai.
# Railway par BG_API_KEY set kar sakte ho.
REMOVE_BG_API_KEY = (
    os.getenv("REMOVE_BG_API_KEY")
    or getattr(_settings, "REMOVE_BG_API_KEY", None)
    or ""
).strip()

# API timeout
REMOVE_BG_TIMEOUT = int(
    os.getenv("REMOVE_BG_TIMEOUT", "300")
)


# ============================================================
# Service
# ============================================================

class BiRefNetService:
    """
    Background removal service.

    Existing backend ke saath compatibility maintain karne ke liye
    class ka naam BiRefNetService aur public method
    remove_background() same rakha gaya hai.

    Actual background removal remove.bg API se hoti hai.
    """

    def __init__(self):
        self.api_url = REMOVE_BG_URL
        self.api_key = REMOVE_BG_API_KEY

        if not self.api_key:
            logger.warning(
                "REMOVE_BG_API_KEY is not configured. "
                "Background removal requests will fail until "
                "the API key is configured."
            )
        else:
            logger.info(
                "remove.bg background removal service initialized."
            )

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    def _remove_background_api(
        self,
        input_path: Path,
        output_path: Path,
    ) -> dict:
        """
        Send image to remove.bg and save transparent PNG.
        """

        if not self.api_key:
            raise RuntimeError(
                "REMOVE_BG_API_KEY is not configured. "
                "Please add your remove.bg API key."
            )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        logger.info(
            "Sending image to remove.bg: %s",
            input_path,
        )

        # ----------------------------------------------------
        # Validate image before sending
        # ----------------------------------------------------

        try:
            with Image.open(input_path) as image:
                width, height = image.size
                image_format = image.format

        except Exception as exc:
            raise RuntimeError(
                f"Could not open input image: {input_path}"
            ) from exc

        logger.info(
            "Input image | format=%s | size=%sx%s",
            image_format,
            width,
            height,
        )

        # ----------------------------------------------------
        # API request
        # ----------------------------------------------------

        try:
            with input_path.open("rb") as image_file:

                response = requests.post(
                    self.api_url,

                    headers={
                        "X-Api-Key": self.api_key,
                    },

                    files={
                        "image_file": (
                            input_path.name,
                            image_file,
                        )
                    },

                    data={
                        "size": "auto",
                    },

                    timeout=REMOVE_BG_TIMEOUT,
                )

        except requests.Timeout as exc:
            raise RuntimeError(
                "remove.bg API request timed out."
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not connect to remove.bg API: {exc}"
            ) from exc

        # ----------------------------------------------------
        # Handle API errors
        # ----------------------------------------------------

        if not response.ok:

            try:
                error_data = response.json()

                errors = error_data.get("errors")

                if errors:
                    error_message = str(errors)
                else:
                    error_message = str(error_data)

            except Exception:
                error_message = response.text

            raise RuntimeError(
                f"remove.bg API request failed "
                f"(HTTP {response.status_code}): "
                f"{error_message}"
            )

        # ----------------------------------------------------
        # Save PNG
        # ----------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            output_path.write_bytes(
                response.content
            )

        except Exception as exc:
            raise RuntimeError(
                f"Could not save output image: {output_path}"
            ) from exc

        # ----------------------------------------------------
        # Validate output
        # ----------------------------------------------------

        try:
            with Image.open(output_path) as result:

                result_width, result_height = result.size

                # Make sure output is actually PNG/RGBA
                result_format = result.format
                result_mode = result.mode

        except Exception as exc:
            raise RuntimeError(
                "remove.bg returned an invalid image."
            ) from exc

        logger.info(
            "Background removed successfully | "
            "format=%s | mode=%s | size=%sx%s | output=%s",
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

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def remove_background(
        self,
        input_path: str | Path,
        output_path: str | Path,
    ) -> dict:
        """
        Remove image background using remove.bg API.

        Parameters
        ----------
        input_path:
            Uploaded/input image.

        output_path:
            Location where transparent PNG will be saved.

        Returns
        -------
        dict
            Output image information.
        """

        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        result = self._remove_background_api(
            input_path=input_path,
            output_path=output_path,
        )

        # Cleanup
        gc.collect()

        return result


# ============================================================
# Global instance
# ============================================================

birefnet_service = BiRefNetService()