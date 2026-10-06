

# from __future__ import annotations

# import base64
# import binascii
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


# # ============================================================
# # Environment / Model Configuration
# # ============================================================

# MODEL_NAME = (
#     os.getenv("BIREFNET_MODEL_NAME")
#     or _settings.BIREFNET_MODEL_NAME
#     or "ZhengPeng7/BiRefNet"
# ).strip()


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


# # ============================================================
# # Hugging Face Authentication
# # ============================================================

# HF_TOKEN = os.getenv("HF_TOKEN", "").strip()


# # ============================================================
# # Hugging Face Revision
# # ============================================================
# #
# # IMPORTANT:
# # This must be an exact Hugging Face commit/revision.
# #
# # Railway can override this value using:
# #
# # BIREFNET_REVISION=...
# #
# # If the Railway variable is missing, the pinned revision below
# # will be used.
# #
# # This prevents Transformers from following the moving "main"
# # branch for the BiRefNet custom Python code.
# #
# # ============================================================

# DEFAULT_BIREFNET_REVISION = (
#     "e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4"
# )

# BIREFNET_REVISION = (
#     os.getenv("BIREFNET_REVISION")
#     or DEFAULT_BIREFNET_REVISION
# ).strip()


# # ============================================================
# # Image Normalization
# # ============================================================

# MEAN = [0.485, 0.456, 0.406]
# STD = [0.229, 0.224, 0.225]


# # ============================================================
# # Device Configuration
# # ============================================================

# if torch.cuda.is_available():

#     try:
#         torch.cuda.set_device(0)

#         torch.backends.cuda.matmul.allow_tf32 = True
#         torch.backends.cudnn.allow_tf32 = True

#     except Exception as exc:

#         logger.warning(
#             "Could not configure CUDA optimizations: %s",
#             exc,
#         )


# DEVICE = torch.device(
#     "cuda"
#     if torch.cuda.is_available()
#     else "cpu"
# )


# # ============================================================
# # Image Resolution
# # ============================================================

# # GPU:
# #   Better quality / higher resolution.
# #
# # CPU:
# #   Lower RAM usage.

# IMAGE_SIZE = (
#     (1024, 1024)
#     if DEVICE.type == "cuda"
#     else (512, 512)
# )


# # ============================================================
# # Image Transform
# # ============================================================

# transform = transforms.Compose(
#     [
#         transforms.Resize(
#             IMAGE_SIZE,
#             interpolation=transforms.InterpolationMode.BILINEAR,
#         ),
#         transforms.ToTensor(),
#         transforms.Normalize(
#             MEAN,
#             STD,
#         ),
#     ]
# )


# # ============================================================
# # Helper
# # ============================================================

# def _extract_prediction(prediction):
#     """
#     Extract the actual segmentation tensor from
#     different possible Transformers output formats.
#     """

#     if isinstance(
#         prediction,
#         (tuple, list),
#     ):

#         if not prediction:
#             raise RuntimeError(
#                 "BiRefNet returned an empty prediction."
#             )

#         prediction = prediction[-1]

#     elif hasattr(
#         prediction,
#         "logits",
#     ):

#         prediction = prediction.logits

#     return prediction


# # ============================================================
# # BiRefNet Service
# # ============================================================

# class BiRefNetService:

#     def __init__(self):

#         self.remote_url = REMOTE_URL

#         self.use_remote = (
#             REMOTE_MODE
#             or bool(self.remote_url)
#         )

#         self.model = None

#         self.dtype = torch.float32

#         logger.info("=" * 60)
#         logger.info("Initializing BiRefNet")
#         logger.info("=" * 60)

#         # ----------------------------------------------------
#         # Remote Mode
#         # ----------------------------------------------------

#         if self.use_remote:

#             if not self.remote_url:

#                 raise RuntimeError(
#                     "BiRefNet remote mode is enabled, "
#                     "but BIREFNET_REMOTE_URL is not configured."
#                 )

#             logger.info(
#                 "Remote BiRefNet mode enabled."
#             )

#             logger.info(
#                 "Remote URL: %s",
#                 self.remote_url,
#             )

#             logger.info(
#                 "Local BiRefNet model will NOT be loaded."
#             )

#             return

#         # ----------------------------------------------------
#         # Local Mode
#         # ----------------------------------------------------

#         logger.info(
#             "BiRefNet local mode enabled."
#         )

#         logger.info(
#             "CUDA available: %s",
#             torch.cuda.is_available(),
#         )

#         logger.info(
#             "Device: %s",
#             DEVICE,
#         )

#         # ----------------------------------------------------
#         # GPU Information
#         # ----------------------------------------------------

#         if DEVICE.type == "cuda":

#             try:

#                 logger.info(
#                     "GPU: %s",
#                     torch.cuda.get_device_name(0),
#                 )

#                 logger.info(
#                     "GPU memory: %.2f GB",
#                     (
#                         torch.cuda
#                         .get_device_properties(0)
#                         .total_memory
#                         / (1024 ** 3)
#                     ),
#                 )

#             except Exception as exc:

#                 logger.warning(
#                     "Could not read GPU information: %s",
#                     exc,
#                 )

#         # ----------------------------------------------------
#         # Model Information
#         # ----------------------------------------------------

#         logger.info(
#             "Model: %s",
#             MODEL_NAME,
#         )

#         logger.info(
#             "BiRefNet revision: %s",
#             BIREFNET_REVISION,
#         )

#         # ----------------------------------------------------
#         # Hugging Face Authentication
#         # ----------------------------------------------------

#         if HF_TOKEN:

#             logger.info(
#                 "Hugging Face token detected."
#             )

#         else:

#             logger.warning(
#                 "HF_TOKEN is not configured. "
#                 "Hugging Face requests will be unauthenticated."
#             )

#         # ----------------------------------------------------
#         # Model Loading Arguments
#         # ----------------------------------------------------
#         #
#         # IMPORTANT:
#         #
#         # Do NOT call from_pretrained() before these arguments
#         # are completely configured.
#         #
#         # from_pretrained() must be called ONLY ONCE.
#         #
#         # ----------------------------------------------------

#         model_kwargs = {
#             "trust_remote_code": True,
#             "revision": BIREFNET_REVISION,
#         }

#         # ----------------------------------------------------
#         # Hugging Face Token
#         # ----------------------------------------------------

#         if HF_TOKEN:

#             model_kwargs["token"] = HF_TOKEN

#         # ----------------------------------------------------
#         # Load Model
#         # ----------------------------------------------------

#         logger.info(
#             "Loading BiRefNet from Hugging Face..."
#         )

#         logger.info(
#             "Using pinned revision: %s",
#             BIREFNET_REVISION,
#         )

#         try:

#             self.model = (
#                 AutoModelForImageSegmentation.from_pretrained(
#                     MODEL_NAME,
#                     **model_kwargs,
#                 )
#             )

#         except Exception:

#             logger.exception(
#                 "Failed to load BiRefNet model."
#             )

#             raise

#         # ----------------------------------------------------
#         # Move Model To Device
#         # ----------------------------------------------------

#         logger.info(
#             "Moving BiRefNet to device: %s",
#             DEVICE,
#         )

#         try:

#             self.model = self.model.to(
#                 DEVICE
#             )

#         except Exception:

#             logger.exception(
#                 "Failed to move BiRefNet to device: %s",
#                 DEVICE,
#             )

#             raise

#         # ----------------------------------------------------
#         # Evaluation Mode
#         # ----------------------------------------------------

#         self.model.eval()

#         # ----------------------------------------------------
#         # Detect Model Dtype
#         # ----------------------------------------------------

#         try:

#             self.dtype = next(
#                 self.model.parameters()
#             ).dtype

#         except StopIteration:

#             logger.warning(
#                 "Could not determine BiRefNet model dtype. "
#                 "Using float32."
#             )

#             self.dtype = torch.float32

#         logger.info(
#             "Model dtype: %s",
#             self.dtype,
#         )

#         # ----------------------------------------------------
#         # Final Status
#         # ----------------------------------------------------

#         logger.info(
#             "BiRefNet loaded successfully."
#         )

#         logger.info(
#             "BiRefNet device: %s",
#             DEVICE,
#         )

#         logger.info("=" * 60)

#     # ========================================================
#     # Remote BiRefNet
#     # ========================================================

#     def _remove_background_remote(
#         self,
#         input_path: str | Path,
#         output_path: str | Path,
#     ) -> dict:

#         if not self.remote_url:

#             raise RuntimeError(
#                 "BIREFNET_REMOTE_URL is not configured."
#             )

#         input_path = Path(
#             input_path
#         )

#         output_path = Path(
#             output_path
#         )

#         if not input_path.exists():

#             raise FileNotFoundError(
#                 f"Input file not found: {input_path}"
#             )

#         logger.info(
#             "Sending image to remote BiRefNet service: %s",
#             self.remote_url,
#         )

#         # ----------------------------------------------------
#         # Read Input
#         # ----------------------------------------------------

#         with input_path.open(
#             "rb"
#         ) as file_obj:

#             file_bytes = file_obj.read()

#         boundary = "----BiRefNetBoundary"

#         # ----------------------------------------------------
#         # Multipart Body
#         # ----------------------------------------------------

#         body = (
#             b"--"
#             + boundary.encode()
#             + b"\r\n"
#             + (
#                 b'Content-Disposition: form-data; '
#                 b'name="file"; filename="'
#             )
#             + input_path.name.encode()
#             + b'"\r\n'
#             + b"Content-Type: application/octet-stream\r\n\r\n"
#             + file_bytes
#             + b"\r\n--"
#             + boundary.encode()
#             + b"--\r\n"
#         )

#         req = request.Request(
#             self.remote_url,
#             data=body,
#             headers={
#                 "Content-Type": (
#                     "multipart/form-data; "
#                     f"boundary={boundary}"
#                 ),
#                 "Accept": (
#                     "image/png, application/json"
#                 ),
#             },
#             method="POST",
#         )

#         # ----------------------------------------------------
#         # Send Request
#         # ----------------------------------------------------

#         try:

#             with request.urlopen(
#                 req,
#                 timeout=600,
#             ) as response:

#                 content_type = (
#                     response.headers.get_content_type()
#                 )

#                 payload = response.read()

#         except error.HTTPError as exc:

#             try:

#                 detail = exc.read().decode(
#                     "utf-8",
#                     errors="replace",
#                 )

#             except Exception:

#                 detail = str(exc)

#             raise RuntimeError(
#                 "Remote BiRefNet request failed: "
#                 f"{detail}"
#             ) from exc

#         except error.URLError as exc:

#             raise RuntimeError(
#                 "Could not connect to remote BiRefNet service: "
#                 f"{exc}"
#             ) from exc

#         except TimeoutError as exc:

#             raise RuntimeError(
#                 "Remote BiRefNet request timed out."
#             ) from exc

#         # ----------------------------------------------------
#         # Output Directory
#         # ----------------------------------------------------

#         output_path.parent.mkdir(
#             parents=True,
#             exist_ok=True,
#         )

#         # ----------------------------------------------------
#         # Direct PNG Response
#         # ----------------------------------------------------

#         if content_type == "image/png":

#             output_path.write_bytes(
#                 payload
#             )

#             logger.info(
#                 "Saved remote result: %s",
#                 output_path,
#             )

#             return {
#                 "filename": output_path.name,
#                 "width": 0,
#                 "height": 0,
#                 "output_path": str(output_path),
#             }

#         # ----------------------------------------------------
#         # JSON Response
#         # ----------------------------------------------------

#         try:

#             data = json.loads(
#                 payload.decode(
#                     "utf-8"
#                 )
#             )

#         except Exception as exc:

#             raise RuntimeError(
#                 "Remote BiRefNet returned an unexpected "
#                 "non-JSON response."
#             ) from exc

#         # ----------------------------------------------------
#         # JSON Image Response
#         # ----------------------------------------------------

#         if (
#             isinstance(data, dict)
#             and "image" in data
#         ):

#             image_data = data["image"]

#             # ------------------------------------------------
#             # Base64 image
#             # ------------------------------------------------

#             if isinstance(
#                 image_data,
#                 str,
#             ):

#                 encoded_data = image_data

#                 # Handle data URLs:
#                 #
#                 # data:image/png;base64,XXXX
#                 #

#                 if "," in encoded_data:

#                     prefix, possible_data = (
#                         encoded_data.split(
#                             ",",
#                             1,
#                         )
#                     )

#                     if (
#                         "base64"
#                         in prefix.lower()
#                     ):

#                         encoded_data = possible_data

#                 try:

#                     decoded = base64.b64decode(
#                         encoded_data,
#                         validate=True,
#                     )

#                     output_path.write_bytes(
#                         decoded
#                     )

#                 except (
#                     ValueError,
#                     binascii.Error,
#                 ):

#                     # Fallback for APIs that return
#                     # raw image data as text.

#                     output_path.write_bytes(
#                         image_data.encode(
#                             "utf-8"
#                         )
#                     )

#             # ------------------------------------------------
#             # Raw bytes
#             # ------------------------------------------------

#             elif isinstance(
#                 image_data,
#                 (
#                     bytes,
#                     bytearray,
#                 ),
#             ):

#                 output_path.write_bytes(
#                     image_data
#                 )

#             else:

#                 raise RuntimeError(
#                     "Remote BiRefNet returned an unsupported "
#                     "'image' value."
#                 )

#             logger.info(
#                 "Saved remote result: %s",
#                 output_path,
#             )

#             return {
#                 "filename": output_path.name,
#                 "width": 0,
#                 "height": 0,
#                 "output_path": str(output_path),
#             }

#         raise RuntimeError(
#             "Remote BiRefNet response was not an image: "
#             f"{data}"
#         )

#     # ========================================================
#     # Local Background Removal
#     # ========================================================

#     def _remove_background_local(
#         self,
#         input_path: Path,
#         output_path: Path,
#     ) -> dict:

#         if self.model is None:

#             raise RuntimeError(
#                 "BiRefNet model is not loaded."
#             )

#         logger.info(
#             "Processing image: %s",
#             input_path,
#         )

#         # ----------------------------------------------------
#         # Load Image
#         # ----------------------------------------------------

#         try:

#             image = Image.open(
#                 input_path
#             ).convert("RGB")

#         except Exception as exc:

#             raise RuntimeError(
#                 f"Could not open image: {input_path}"
#             ) from exc

#         original_size = image.size

#         # ----------------------------------------------------
#         # Transform Image
#         # ----------------------------------------------------

#         tensor = transform(
#             image
#         )

#         tensor = tensor.unsqueeze(
#             0
#         )

#         tensor = tensor.to(
#             device=DEVICE,
#             dtype=self.dtype,
#         )

#         # ----------------------------------------------------
#         # Model Inference
#         # ----------------------------------------------------

#         try:

#             with torch.inference_mode():

#                 prediction = self.model(
#                     tensor
#                 )

#         except Exception:

#             logger.exception(
#                 "BiRefNet inference failed."
#             )

#             raise

#         # ----------------------------------------------------
#         # Extract Prediction
#         # ----------------------------------------------------

#         prediction = _extract_prediction(
#             prediction
#         )

#         # ----------------------------------------------------
#         # Validate Prediction
#         # ----------------------------------------------------

#         if not isinstance(
#             prediction,
#             torch.Tensor,
#         ):

#             raise RuntimeError(
#                 "BiRefNet returned an unsupported "
#                 "prediction type: "
#                 f"{type(prediction)}"
#             )

#         # ----------------------------------------------------
#         # Convert To Mask
#         # ----------------------------------------------------

#         prediction = prediction.float()

#         prediction = prediction.sigmoid()

#         prediction = prediction.squeeze()

#         # ----------------------------------------------------
#         # Validate Mask Shape
#         # ----------------------------------------------------

#         if prediction.ndim != 2:

#             raise RuntimeError(
#                 "Unexpected BiRefNet mask shape: "
#                 f"{tuple(prediction.shape)}"
#             )

#         # ----------------------------------------------------
#         # Convert Tensor To PIL
#         # ----------------------------------------------------

#         mask = transforms.ToPILImage()(
#             prediction.cpu()
#         )

#         # ----------------------------------------------------
#         # Restore Original Resolution
#         # ----------------------------------------------------

#         mask = mask.resize(
#             original_size,
#             Image.Resampling.LANCZOS,
#         )

#         # ----------------------------------------------------
#         # Apply Alpha Channel
#         # ----------------------------------------------------

#         result = image.convert(
#             "RGBA"
#         )

#         result.putalpha(
#             mask
#         )

#         # ----------------------------------------------------
#         # Create Output Directory
#         # ----------------------------------------------------

#         output_path.parent.mkdir(
#             parents=True,
#             exist_ok=True,
#         )

#         # ----------------------------------------------------
#         # Save PNG
#         # ----------------------------------------------------

#         result.save(
#             output_path,
#             format="PNG",
#         )

#         logger.info(
#             "Saved background-removed image: %s",
#             output_path,
#         )

#         # ----------------------------------------------------
#         # Release Temporary GPU Memory
#         # ----------------------------------------------------

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

#     # ========================================================
#     # Main Background Removal
#     # ========================================================

#     def remove_background(
#         self,
#         input_path: str | Path,
#         output_path: str | Path,
#     ) -> dict:

#         input_path = Path(
#             input_path
#         )

#         output_path = Path(
#             output_path
#         )

#         # ----------------------------------------------------
#         # Validate Input
#         # ----------------------------------------------------

#         if not input_path.exists():

#             raise FileNotFoundError(
#                 f"Input file not found: {input_path}"
#             )

#         # ----------------------------------------------------
#         # Remote Mode
#         # ----------------------------------------------------

#         if self.use_remote:

#             return self._remove_background_remote(
#                 input_path,
#                 output_path,
#             )

#         # ----------------------------------------------------
#         # Local Mode
#         # ----------------------------------------------------

#         return self._remove_background_local(
#             input_path,
#             output_path,
#         )


# # ============================================================
# # Global BiRefNet Service
# # ============================================================

# birefnet_service = BiRefNetService()






from __future__ import annotations

import base64
import binascii
import gc
import json
import logging
import os
import threading
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
# Device
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if DEVICE.type == "cuda":
    try:
        torch.cuda.set_device(0)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    except Exception as exc:
        logger.warning("Could not configure CUDA optimizations: %s", exc)
else:
    # Railway containers share CPUs; fewer threads = lower RAM/CPU spikes.
    try:
        torch.set_num_threads(int(os.getenv("BIREFNET_THREADS", "2")))
    except Exception:
        pass


# ============================================================
# Configuration (all overridable from Railway variables)
# ============================================================

FULL_MODEL = "ZhengPeng7/BiRefNet"
LITE_MODEL = "ZhengPeng7/BiRefNet_lite"

# On CPU the lite model is used unless you explicitly set a model name.
MODEL_NAME = (
    os.getenv("BIREFNET_MODEL_NAME")
    or getattr(_settings, "BIREFNET_MODEL_NAME", None)
    or (FULL_MODEL if DEVICE.type == "cuda" else LITE_MODEL)
).strip()

REMOTE_URL = (
    os.getenv("BIREFNET_REMOTE_URL")
    or getattr(_settings, "BIREFNET_REMOTE_URL", None)
    or ""
).strip()

REMOTE_MODE = (
    os.getenv("BIREFNET_MODE")
    or getattr(_settings, "BIREFNET_MODE", None)
    or "local"
).strip().lower() == "remote"

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# The pinned commit below belongs ONLY to the full BiRefNet repo.
# For any other model (e.g. BiRefNet_lite) no revision is sent unless
# you set BIREFNET_REVISION yourself, otherwise HF returns "revision not found".
DEFAULT_BIREFNET_REVISION = "e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4"

BIREFNET_REVISION = (
    os.getenv("BIREFNET_REVISION")
    or (DEFAULT_BIREFNET_REVISION if MODEL_NAME == FULL_MODEL else "")
).strip()

# false (default): model loads on first request, so the app always starts
# and passes the healthcheck. true: load at startup.
PRELOAD = os.getenv("BIREFNET_PRELOAD", "false").strip().lower() == "true"

# CPU only: bfloat16 roughly halves model RAM. Default stays float32.
CPU_DTYPE_NAME = os.getenv("BIREFNET_DTYPE", "float32").strip().lower()

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

_default_size = 1024 if DEVICE.type == "cuda" else 512
_size = int(os.getenv("BIREFNET_IMAGE_SIZE", str(_default_size)))
IMAGE_SIZE = (_size, _size)

transform = transforms.Compose(
    [
        transforms.Resize(
            IMAGE_SIZE,
            interpolation=transforms.InterpolationMode.BILINEAR,
        ),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ]
)


# ============================================================
# Helpers
# ============================================================

def _extract_prediction(prediction):
    """Get the segmentation tensor from different output formats."""
    if isinstance(prediction, (tuple, list)):
        if not prediction:
            raise RuntimeError("BiRefNet returned an empty prediction.")
        return prediction[-1]

    if hasattr(prediction, "logits"):
        return prediction.logits

    return prediction


# ============================================================
# Service
# ============================================================

class BiRefNetService:

    def __init__(self):
        self.remote_url = REMOTE_URL
        self.use_remote = REMOTE_MODE or bool(self.remote_url)

        self.model = None
        self.dtype = torch.float32

        self._load_lock = threading.Lock()
        self._infer_lock = threading.Lock()  # one inference at a time = no RAM spikes

        logger.info("Initializing BiRefNet service")

        if self.use_remote:
            if not self.remote_url:
                raise RuntimeError(
                    "BiRefNet remote mode is enabled, "
                    "but BIREFNET_REMOTE_URL is not configured."
                )
            logger.info("Remote mode enabled: %s", self.remote_url)
            logger.info("Local BiRefNet model will NOT be loaded.")
            return

        logger.info(
            "Local mode | device=%s | model=%s | revision=%s | preload=%s",
            DEVICE,
            MODEL_NAME,
            BIREFNET_REVISION or "default",
            PRELOAD,
        )

        if PRELOAD:
            self.load_model()
        else:
            logger.info("Model will be loaded lazily on first request.")

    # --------------------------------------------------------
    # Model loading
    # --------------------------------------------------------

    def load_model(self) -> None:
        """Load the model once (thread-safe)."""
        if self.model is not None:
            return

        with self._load_lock:
            if self.model is not None:
                return

            if DEVICE.type == "cuda":
                try:
                    logger.info("GPU: %s", torch.cuda.get_device_name(0))
                except Exception as exc:
                    logger.warning("Could not read GPU information: %s", exc)

            # NOTE: do not pass low_cpu_mem_usage=True here. BiRefNet's custom
            # code builds tensors in __init__ and breaks with meta-device init.
            model_kwargs = {"trust_remote_code": True}

            if BIREFNET_REVISION:
                model_kwargs["revision"] = BIREFNET_REVISION

            if HF_TOKEN:
                model_kwargs["token"] = HF_TOKEN
            else:
                logger.warning(
                    "HF_TOKEN is not configured. Requests will be unauthenticated."
                )

            logger.info("Loading BiRefNet from Hugging Face...")

            try:
                model = AutoModelForImageSegmentation.from_pretrained(
                    MODEL_NAME,
                    **model_kwargs,
                )
            except Exception:
                logger.exception("Failed to load BiRefNet model.")
                raise

            model.eval()

            for param in model.parameters():
                param.requires_grad_(False)

            if DEVICE.type == "cpu" and CPU_DTYPE_NAME == "bfloat16":
                model = model.to(dtype=torch.bfloat16)

            try:
                model = model.to(DEVICE)
            except Exception:
                logger.exception("Failed to move BiRefNet to device: %s", DEVICE)
                raise

            try:
                self.dtype = next(model.parameters()).dtype
            except StopIteration:
                self.dtype = torch.float32

            self.model = model
            gc.collect()

            logger.info(
                "BiRefNet loaded successfully | device=%s | dtype=%s",
                DEVICE,
                self.dtype,
            )

    # --------------------------------------------------------
    # Remote
    # --------------------------------------------------------

    def _remove_background_remote(
        self,
        input_path: Path,
        output_path: Path,
    ) -> dict:

        logger.info("Sending image to remote BiRefNet: %s", self.remote_url)

        file_bytes = input_path.read_bytes()

        boundary = "----BiRefNetBoundary"

        body = (
            b"--" + boundary.encode() + b"\r\n"
            + b'Content-Disposition: form-data; name="file"; filename="'
            + input_path.name.encode()
            + b'"\r\n'
            + b"Content-Type: application/octet-stream\r\n\r\n"
            + file_bytes
            + b"\r\n--" + boundary.encode() + b"--\r\n"
        )

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "image/png, application/json",
            # Lets ngrok free tunnels skip the browser warning page.
            "ngrok-skip-browser-warning": "true",
        }

        req = request.Request(
            self.remote_url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=600) as response:
                content_type = response.headers.get_content_type()
                payload = response.read()

        except error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"Remote BiRefNet request failed: {detail}") from exc

        except error.URLError as exc:
            raise RuntimeError(
                f"Could not connect to remote BiRefNet service: {exc}"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError("Remote BiRefNet request timed out.") from exc

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Direct image response
        if content_type.startswith("image/"):
            output_path.write_bytes(payload)

        # JSON response
        else:
            try:
                data = json.loads(payload.decode("utf-8"))
            except Exception as exc:
                raise RuntimeError(
                    "Remote BiRefNet returned an unexpected non-JSON response."
                ) from exc

            if not isinstance(data, dict) or "image" not in data:
                raise RuntimeError(
                    f"Remote BiRefNet response was not an image: {data}"
                )

            image_data = data["image"]

            if isinstance(image_data, str):
                encoded = image_data

                # data:image/png;base64,XXXX
                if "," in encoded:
                    prefix, possible = encoded.split(",", 1)
                    if "base64" in prefix.lower():
                        encoded = possible

                try:
                    output_path.write_bytes(base64.b64decode(encoded, validate=True))
                except (ValueError, binascii.Error) as exc:
                    raise RuntimeError(
                        "Remote BiRefNet returned invalid base64 image data."
                    ) from exc

            elif isinstance(image_data, (bytes, bytearray)):
                output_path.write_bytes(bytes(image_data))

            else:
                raise RuntimeError(
                    "Remote BiRefNet returned an unsupported 'image' value."
                )

        width = height = 0
        try:
            with Image.open(output_path) as img:
                width, height = img.size
        except Exception:
            logger.warning("Remote result could not be read as an image.")

        logger.info("Saved remote result: %s", output_path)

        return {
            "filename": output_path.name,
            "width": width,
            "height": height,
            "output_path": str(output_path),
        }

    # --------------------------------------------------------
    # Local
    # --------------------------------------------------------

    def _remove_background_local(
        self,
        input_path: Path,
        output_path: Path,
    ) -> dict:

        self.load_model()

        if self.model is None:
            raise RuntimeError("BiRefNet model is not loaded.")

        logger.info("Processing image: %s", input_path)

        try:
            image = Image.open(input_path).convert("RGB")
        except Exception as exc:
            raise RuntimeError(f"Could not open image: {input_path}") from exc

        original_size = image.size

        tensor = transform(image).unsqueeze(0).to(device=DEVICE, dtype=self.dtype)

        try:
            with self._infer_lock:
                with torch.inference_mode():
                    prediction = self.model(tensor)
        except Exception:
            logger.exception("BiRefNet inference failed.")
            raise

        prediction = _extract_prediction(prediction)

        if not isinstance(prediction, torch.Tensor):
            raise RuntimeError(
                f"BiRefNet returned an unsupported prediction type: {type(prediction)}"
            )

        prediction = prediction.float().sigmoid().squeeze()

        if prediction.ndim != 2:
            raise RuntimeError(
                f"Unexpected BiRefNet mask shape: {tuple(prediction.shape)}"
            )

        mask = transforms.ToPILImage()(prediction.cpu())
        mask = mask.resize(original_size, Image.Resampling.LANCZOS)

        result = image.convert("RGBA")
        result.putalpha(mask)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path, format="PNG")

        logger.info("Saved background-removed image: %s", output_path)

        # Free temporary memory
        del tensor, prediction, mask, result, image
        gc.collect()

        if DEVICE.type == "cuda":
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

        return {
            "filename": output_path.name,
            "width": original_size[0],
            "height": original_size[1],
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

        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if self.use_remote:
            return self._remove_background_remote(input_path, output_path)

        return self._remove_background_local(input_path, output_path)


# ============================================================
# Global instance
# ============================================================
# Creating it no longer loads the model (unless BIREFNET_PRELOAD=true),
# so importing this module cannot crash the container anymore.

birefnet_service = BiRefNetService()