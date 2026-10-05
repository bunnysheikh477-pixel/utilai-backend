




# # from __future__ import annotations

# # import json
# # import logging
# # import os
# # from pathlib import Path
# # from urllib import error, request

# # import torch
# # from PIL import Image
# # from torchvision import transforms
# # from transformers import AutoModelForImageSegmentation

# # from app.core.config import get_settings


# # logger = logging.getLogger(__name__)

# # _settings = get_settings()


# # # ============================================================
# # # Environment / Model Configuration
# # # ============================================================

# # MODEL_NAME = (
# #     os.getenv("BIREFNET_MODEL_NAME")
# #     or _settings.BIREFNET_MODEL_NAME
# #     or "ZhengPeng7/BiRefNet"
# # )

# # REMOTE_URL = (
# #     os.getenv("BIREFNET_REMOTE_URL")
# #     or _settings.BIREFNET_REMOTE_URL
# #     or ""
# # ).strip()

# # REMOTE_MODE = (
# #     os.getenv("BIREFNET_MODE")
# #     or _settings.BIREFNET_MODE
# #     or "local"
# # ).strip().lower() == "remote"


# # # Hugging Face token
# # #
# # # IMPORTANT:
# # # Do NOT put the real token directly in this file.
# # # Railway should provide it through:
# # #
# # # HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
# # #
# # HF_TOKEN = os.getenv("HF_TOKEN", "").strip()


# # # Optional model revision.
# # #
# # # You can leave this empty for now.
# # # Later you can set a specific Hugging Face commit/revision
# # # for better reproducibility and security.
# # BIREFNET_REVISION = os.getenv(
# #     "BIREFNET_REVISION",
# #     "",
# # ).strip()


# # MEAN = [0.485, 0.456, 0.406]
# # STD = [0.229, 0.224, 0.225]


# # # ============================================================
# # # Device Configuration
# # # ============================================================

# # if torch.cuda.is_available():
# #     torch.cuda.set_device(0)

# #     torch.backends.cuda.matmul.allow_tf32 = True
# #     torch.backends.cudnn.allow_tf32 = True


# # DEVICE = torch.device(
# #     "cuda" if torch.cuda.is_available() else "cpu"
# # )


# # # CPU -> smaller image to reduce RAM usage
# # # GPU -> larger image for better quality
# # IMAGE_SIZE = (
# #     (1024, 1024)
# #     if DEVICE.type == "cuda"
# #     else (512, 512)
# # )


# # # ============================================================
# # # Image Transform
# # # ============================================================

# # transform = transforms.Compose(
# #     [
# #         transforms.Resize(IMAGE_SIZE),
# #         transforms.ToTensor(),
# #         transforms.Normalize(MEAN, STD),
# #     ]
# # )


# # # ============================================================
# # # BiRefNet Service
# # # ============================================================

# # class BiRefNetService:

# #     def __init__(self):
# #         self.remote_url = REMOTE_URL
# #         self.use_remote = (
# #             REMOTE_MODE
# #             or bool(self.remote_url)
# #         )

# #         logger.info("=" * 60)
# #         logger.info("Initializing BiRefNet")
# #         logger.info("=" * 60)

# #         # ----------------------------------------------------
# #         # Remote mode
# #         # ----------------------------------------------------

# #         if self.use_remote:
# #             logger.info(
# #                 "Remote BiRefNet mode enabled."
# #             )

# #             logger.info(
# #                 "Remote URL: %s",
# #                 self.remote_url,
# #             )

# #             self.model = None
# #             self.dtype = torch.float32

# #             return

# #         # ----------------------------------------------------
# #         # Local model mode
# #         # ----------------------------------------------------

# #         logger.info(
# #             "CUDA available: %s",
# #             torch.cuda.is_available(),
# #         )

# #         logger.info(
# #             "Device: %s",
# #             DEVICE,
# #         )

# #         if torch.cuda.is_available():
# #             logger.info(
# #                 "GPU: %s",
# #                 torch.cuda.get_device_name(0),
# #             )

# #         logger.info(
# #             "Model: %s",
# #             MODEL_NAME,
# #         )

# #         # ----------------------------------------------------
# #         # Hugging Face authentication
# #         # ----------------------------------------------------

# #         if HF_TOKEN:
# #             logger.info(
# #                 "Hugging Face token detected."
# #             )
# #         else:
# #             logger.warning(
# #                 "HF_TOKEN is not configured. "
# #                 "Hugging Face requests will be unauthenticated."
# #             )

# #         # ----------------------------------------------------
# #         # Model loading arguments
# #         # ----------------------------------------------------

# #         model_kwargs = {
# #             "trust_remote_code": True,
# #         }

# #         # Only send token when it exists.
# #         #
# #         # This prevents passing an empty token to
# #         # transformers/Hugging Face.
# #         if HF_TOKEN:
# #             model_kwargs["token"] = HF_TOKEN

# #         # Optional revision pinning.
# #         #
# #         # Example:
# #         # BIREFNET_REVISION=<commit-hash>
# #         #
# #         # We intentionally do not hardcode a fake revision.
# #         if BIREFNET_REVISION:
# #             model_kwargs["revision"] = BIREFNET_REVISION

# #             logger.info(
# #                 "BiRefNet revision: %s",
# #                 BIREFNET_REVISION,
# #             )

# #         # ----------------------------------------------------
# #         # Download / load BiRefNet
# #         # ----------------------------------------------------

# #         logger.info(
# #             "Loading BiRefNet from Hugging Face..."
# #         )

# #         self.model = (
# #             AutoModelForImageSegmentation.from_pretrained(
# #                 MODEL_NAME,
# #                 **model_kwargs,
# #             )
# #         )

# #         # ----------------------------------------------------
# #         # Move model to CPU/GPU
# #         # ----------------------------------------------------

# #         self.model = self.model.to(DEVICE)

# #         self.model.eval()

# #         # ----------------------------------------------------
# #         # Detect model dtype
# #         # ----------------------------------------------------

# #         self.dtype = next(
# #             self.model.parameters()
# #         ).dtype

# #         logger.info(
# #             "Model dtype: %s",
# #             self.dtype,
# #         )

# #         logger.info(
# #             "BiRefNet loaded successfully."
# #         )

# #         logger.info("=" * 60)


# #     # ========================================================
# #     # Remote BiRefNet
# #     # ========================================================

# #     def _remove_background_remote(
# #         self,
# #         input_path: str | Path,
# #         output_path: str | Path,
# #     ) -> dict:

# #         if not self.remote_url:
# #             raise RuntimeError(
# #                 "BIREFNET_REMOTE_URL is not configured."
# #             )

# #         input_path = Path(input_path)
# #         output_path = Path(output_path)

# #         if not input_path.exists():
# #             raise FileNotFoundError(
# #                 f"Input file not found: {input_path}"
# #             )

# #         logger.info(
# #             "Sending image to remote BiRefNet service: %s",
# #             self.remote_url,
# #         )

# #         with input_path.open("rb") as file_obj:
# #             file_bytes = file_obj.read()

# #         boundary = "----BiRefNetBoundary"

# #         body = (
# #             b"--"
# #             + boundary.encode()
# #             + b"\r\n"
# #             + b'Content-Disposition: form-data; '
# #               b'name="file"; filename="'
# #             + input_path.name.encode()
# #             + b'"\r\n'
# #             + b"Content-Type: image/png\r\n\r\n"
# #             + file_bytes
# #             + b"\r\n--"
# #             + boundary.encode()
# #             + b"--\r\n"
# #         )

# #         req = request.Request(
# #             self.remote_url,
# #             data=body,
# #             headers={
# #                 "Content-Type": (
# #                     "multipart/form-data; "
# #                     f"boundary={boundary}"
# #                 ),
# #                 "Accept": (
# #                     "image/png, application/json"
# #                 ),
# #             },
# #             method="POST",
# #         )

# #         try:
# #             with request.urlopen(
# #                 req,
# #                 timeout=600,
# #             ) as response:

# #                 content_type = (
# #                     response.headers.get_content_type()
# #                 )

# #                 payload = response.read()

# #         except error.HTTPError as exc:

# #             try:
# #                 detail = exc.read().decode(
# #                     "utf-8",
# #                     errors="replace",
# #                 )
# #             except Exception:
# #                 detail = str(exc)

# #             raise RuntimeError(
# #                 "Remote BiRefNet request failed: "
# #                 f"{detail}"
# #             ) from exc

# #         output_path.parent.mkdir(
# #             parents=True,
# #             exist_ok=True,
# #         )

# #         # ----------------------------------------------------
# #         # PNG response
# #         # ----------------------------------------------------

# #         if content_type == "image/png":

# #             output_path.write_bytes(
# #                 payload
# #             )

# #             logger.info(
# #                 "Saved remote result: %s",
# #                 output_path,
# #             )

# #             return {
# #                 "filename": output_path.name,
# #                 "width": 0,
# #                 "height": 0,
# #                 "output_path": str(output_path),
# #             }

# #         # ----------------------------------------------------
# #         # JSON response
# #         # ----------------------------------------------------

# #         try:
# #             data = json.loads(
# #                 payload.decode("utf-8")
# #             )

# #         except Exception as exc:

# #             raise RuntimeError(
# #                 "Remote BiRefNet returned "
# #                 "an unexpected response."
# #             ) from exc

# #         if (
# #             isinstance(data, dict)
# #             and "image" in data
# #         ):

# #             image_bytes = data["image"]

# #             if isinstance(
# #                 image_bytes,
# #                 str,
# #             ):
# #                 output_path.write_bytes(
# #                     image_bytes.encode("utf-8")
# #                 )
# #             else:
# #                 output_path.write_bytes(
# #                     image_bytes
# #                 )

# #             logger.info(
# #                 "Saved remote result: %s",
# #                 output_path,
# #             )

# #             return {
# #                 "filename": output_path.name,
# #                 "width": 0,
# #                 "height": 0,
# #                 "output_path": str(output_path),
# #             }

# #         raise RuntimeError(
# #             "Remote BiRefNet response was not "
# #             f"an image: {data}"
# #         )


# #     # ========================================================
# #     # Main Background Removal
# #     # ========================================================

# #     def remove_background(
# #         self,
# #         input_path: str | Path,
# #         output_path: str | Path,
# #     ) -> dict:

# #         # ----------------------------------------------------
# #         # Remote mode
# #         # ----------------------------------------------------

# #         if self.use_remote:

# #             return self._remove_background_remote(
# #                 input_path,
# #                 output_path,
# #             )

# #         # ----------------------------------------------------
# #         # Local mode
# #         # ----------------------------------------------------

# #         input_path = Path(input_path)
# #         output_path = Path(output_path)

# #         if not input_path.exists():
# #             raise FileNotFoundError(
# #                 f"Input file not found: {input_path}"
# #             )

# #         logger.info(
# #             "Processing: %s",
# #             input_path,
# #         )

# #         # ----------------------------------------------------
# #         # Load image
# #         # ----------------------------------------------------

# #         image = Image.open(
# #             input_path
# #         ).convert("RGB")

# #         original_size = image.size

# #         # ----------------------------------------------------
# #         # Transform image
# #         # ----------------------------------------------------

# #         tensor = transform(image)

# #         tensor = tensor.unsqueeze(0)

# #         tensor = tensor.to(
# #             device=DEVICE,
# #             dtype=self.dtype,
# #         )

# #         # ----------------------------------------------------
# #         # Model inference
# #         # ----------------------------------------------------

# #         with torch.inference_mode():

# #             prediction = self.model(
# #                 tensor
# #             )

# #             if isinstance(
# #                 prediction,
# #                 (tuple, list),
# #             ):
# #                 prediction = prediction[-1]

# #             elif hasattr(
# #                 prediction,
# #                 "logits",
# #             ):
# #                 prediction = (
# #                     prediction.logits
# #                 )

# #         # ----------------------------------------------------
# #         # Convert prediction to mask
# #         # ----------------------------------------------------

# #         prediction = prediction.float()

# #         prediction = prediction.sigmoid()

# #         prediction = prediction.squeeze()

# #         mask = transforms.ToPILImage()(
# #             prediction.cpu()
# #         )

# #         # ----------------------------------------------------
# #         # Restore original image size
# #         # ----------------------------------------------------

# #         mask = mask.resize(
# #             original_size,
# #             Image.Resampling.LANCZOS,
# #         )

# #         # ----------------------------------------------------
# #         # Apply alpha mask
# #         # ----------------------------------------------------

# #         result = image.convert(
# #             "RGBA"
# #         )

# #         result.putalpha(
# #             mask
# #         )

# #         # ----------------------------------------------------
# #         # Save output
# #         # ----------------------------------------------------

# #         output_path.parent.mkdir(
# #             parents=True,
# #             exist_ok=True,
# #         )

# #         result.save(
# #             output_path,
# #             format="PNG",
# #         )

# #         logger.info(
# #             "Saved result: %s",
# #             output_path,
# #         )

# #         return {
# #             "filename": output_path.name,
# #             "width": original_size[0],
# #             "height": original_size[1],
# #             "output_path": str(output_path),
# #         }


# # # ============================================================
# # # Global BiRefNet Service
# # # ============================================================

# # birefnet_service = BiRefNetService()






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


# # ============================================================
# # Environment / Model Configuration
# # ============================================================

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


# # Hugging Face token.
# #
# # Set this in Railway Variables:
# #
# # HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
# #
# # Never hard-code the real token here.
# HF_TOKEN = os.getenv("HF_TOKEN", "").strip()


# # Optional Hugging Face revision.
# #
# # Recommended for production:
# #
# # BIREFNET_REVISION=<exact-commit-hash>
# #
# # Do NOT put a random/fake hash here.
# BIREFNET_REVISION = os.getenv(
#     "BIREFNET_REVISION",
#     "",
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


# # GPU gets higher inference resolution.
# # CPU gets smaller resolution to reduce RAM usage.
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
#         # Remote mode
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
#                 "Local BiRefNet model will not be loaded."
#             )

#             return

#         # ----------------------------------------------------
#         # Local mode
#         # ----------------------------------------------------

#         logger.info(
#             "CUDA available: %s",
#             torch.cuda.is_available(),
#         )

#         logger.info(
#             "Device: %s",
#             DEVICE,
#         )

#         if DEVICE.type == "cuda":

#             try:
#                 logger.info(
#                     "GPU: %s",
#                     torch.cuda.get_device_name(0),
#                 )

#                 logger.info(
#                     "GPU memory: %.2f GB",
#                     torch.cuda.get_device_properties(0).total_memory
#                     / (1024 ** 3),
#                 )

#             except Exception as exc:

#                 logger.warning(
#                     "Could not read GPU information: %s",
#                     exc,
#                 )

#         logger.info(
#             "Model: %s",
#             MODEL_NAME,
#         )

#         # ----------------------------------------------------
#         # Hugging Face authentication
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
#         # Model loading arguments
#         # ----------------------------------------------------

#         model_kwargs = {
#             "trust_remote_code": True,
#              "revision": BIREFNET_REVISION,
#              "code_revision": BIREFNET_REVISION,
#         }

#         # Add Hugging Face token only when available.
#         if HF_TOKEN:

#             model_kwargs["token"] = HF_TOKEN

#         self.model = AutoModelForImageSegmentation.from_pretrained(
#              MODEL_NAME,
#              **model_kwargs,
#         )    

#         # ----------------------------------------------------
#         # Revision pinning
#         # ----------------------------------------------------

#         if BIREFNET_REVISION:

#             model_kwargs["revision"] = (
#                 BIREFNET_REVISION
#             )

#             logger.info(
#                 "BiRefNet revision pinned to: %s",
#                 BIREFNET_REVISION,
#             )

#         else:

#             logger.warning(
#                 "BIREFNET_REVISION is not configured. "
#                 "BiRefNet custom code will use the repository's "
#                 "current revision. For production, pin an exact "
#                 "Hugging Face commit hash."
#             )

#         # ----------------------------------------------------
#         # Load model
#         # ----------------------------------------------------

#         logger.info(
#             "Loading BiRefNet from Hugging Face..."
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
#         # Move model to device
#         # ----------------------------------------------------

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
#         # Evaluation mode
#         # ----------------------------------------------------

#         self.model.eval()

#         # ----------------------------------------------------
#         # Detect model dtype
#         # ----------------------------------------------------

#         try:

#             self.dtype = next(
#                 self.model.parameters()
#             ).dtype

#         except StopIteration:

#             logger.warning(
#                 "Could not determine model dtype. "
#                 "Using float32."
#             )

#             self.dtype = torch.float32

#         logger.info(
#             "Model dtype: %s",
#             self.dtype,
#         )

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
#         # Read image
#         # ----------------------------------------------------

#         with input_path.open("rb") as file_obj:

#             file_bytes = file_obj.read()

#         boundary = "----BiRefNetBoundary"

#         # ----------------------------------------------------
#         # Multipart request body
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
#             + b"Content-Type: image/png\r\n\r\n"
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
#         # Send request
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
#         # Create output directory
#         # ----------------------------------------------------

#         output_path.parent.mkdir(
#             parents=True,
#             exist_ok=True,
#         )

#         # ----------------------------------------------------
#         # PNG response
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
#         # JSON response
#         # ----------------------------------------------------

#         try:

#             data = json.loads(
#                 payload.decode("utf-8")
#             )

#         except Exception as exc:

#             raise RuntimeError(
#                 "Remote BiRefNet returned an unexpected "
#                 "non-JSON response."
#             ) from exc

#         # ----------------------------------------------------
#         # JSON image response
#         # ----------------------------------------------------

#         if (
#             isinstance(data, dict)
#             and "image" in data
#         ):

#             image_data = data["image"]

#             # If the remote service returns a path/string,
#             # this branch assumes it contains image bytes
#             # encoded as text, matching your previous API.
#             if isinstance(
#                 image_data,
#                 str,
#             ):

#                 output_path.write_bytes(
#                     image_data.encode("utf-8")
#                 )

#             elif isinstance(
#                 image_data,
#                 (bytes, bytearray),
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

#         # ----------------------------------------------------
#         # Load image
#         # ----------------------------------------------------

#         logger.info(
#             "Processing: %s",
#             input_path,
#         )

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
#         # Transform
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
#         # Inference
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
#         # Extract prediction
#         # ----------------------------------------------------

#         if isinstance(
#             prediction,
#             (tuple, list),
#         ):

#             prediction = prediction[-1]

#         elif hasattr(
#             prediction,
#             "logits",
#         ):

#             prediction = (
#                 prediction.logits
#             )

#         # ----------------------------------------------------
#         # Validate prediction
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
#         # Convert prediction to mask
#         # ----------------------------------------------------

#         prediction = prediction.float()

#         prediction = prediction.sigmoid()

#         prediction = prediction.squeeze()

#         # Make sure the mask has the expected dimensions.
#         if prediction.ndim != 2:

#             raise RuntimeError(
#                 "Unexpected BiRefNet mask shape: "
#                 f"{tuple(prediction.shape)}"
#             )

#         mask = transforms.ToPILImage()(
#             prediction.cpu()
#         )

#         # ----------------------------------------------------
#         # Restore original resolution
#         # ----------------------------------------------------

#         mask = mask.resize(
#             original_size,
#             Image.Resampling.LANCZOS,
#         )

#         # ----------------------------------------------------
#         # Apply alpha channel
#         # ----------------------------------------------------

#         result = image.convert(
#             "RGBA"
#         )

#         result.putalpha(
#             mask
#         )

#         # ----------------------------------------------------
#         # Save result
#         # ----------------------------------------------------

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

#         # ----------------------------------------------------
#         # Release temporary GPU memory
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
#         # Validate input
#         # ----------------------------------------------------

#         if not input_path.exists():

#             raise FileNotFoundError(
#                 f"Input file not found: {input_path}"
#             )

#         # ----------------------------------------------------
#         # Remote mode
#         # ----------------------------------------------------

#         if self.use_remote:

#             return self._remove_background_remote(
#                 input_path,
#                 output_path,
#             )

#         # ----------------------------------------------------
#         # Local mode
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
).strip()


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


# ============================================================
# Hugging Face Authentication
# ============================================================

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()


# ============================================================
# Hugging Face Revision
# ============================================================
#
# IMPORTANT:
# This must be an exact Hugging Face commit/revision.
#
# Railway can override this value using:
#
# BIREFNET_REVISION=...
#
# If the Railway variable is missing, the pinned revision below
# will be used.
#
# This prevents Transformers from following the moving "main"
# branch for the BiRefNet custom Python code.
#
# ============================================================

DEFAULT_BIREFNET_REVISION = (
    "e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4"
)

BIREFNET_REVISION = (
    os.getenv("BIREFNET_REVISION")
    or DEFAULT_BIREFNET_REVISION
).strip()


# ============================================================
# Image Normalization
# ============================================================

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


# ============================================================
# Device Configuration
# ============================================================

if torch.cuda.is_available():

    try:
        torch.cuda.set_device(0)

        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    except Exception as exc:

        logger.warning(
            "Could not configure CUDA optimizations: %s",
            exc,
        )


DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# Image Resolution
# ============================================================

# GPU:
#   Better quality / higher resolution.
#
# CPU:
#   Lower RAM usage.

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
        transforms.Resize(
            IMAGE_SIZE,
            interpolation=transforms.InterpolationMode.BILINEAR,
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            MEAN,
            STD,
        ),
    ]
)


# ============================================================
# Helper
# ============================================================

def _extract_prediction(prediction):
    """
    Extract the actual segmentation tensor from
    different possible Transformers output formats.
    """

    if isinstance(
        prediction,
        (tuple, list),
    ):

        if not prediction:
            raise RuntimeError(
                "BiRefNet returned an empty prediction."
            )

        prediction = prediction[-1]

    elif hasattr(
        prediction,
        "logits",
    ):

        prediction = prediction.logits

    return prediction


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

        self.model = None

        self.dtype = torch.float32

        logger.info("=" * 60)
        logger.info("Initializing BiRefNet")
        logger.info("=" * 60)

        # ----------------------------------------------------
        # Remote Mode
        # ----------------------------------------------------

        if self.use_remote:

            if not self.remote_url:

                raise RuntimeError(
                    "BiRefNet remote mode is enabled, "
                    "but BIREFNET_REMOTE_URL is not configured."
                )

            logger.info(
                "Remote BiRefNet mode enabled."
            )

            logger.info(
                "Remote URL: %s",
                self.remote_url,
            )

            logger.info(
                "Local BiRefNet model will NOT be loaded."
            )

            return

        # ----------------------------------------------------
        # Local Mode
        # ----------------------------------------------------

        logger.info(
            "BiRefNet local mode enabled."
        )

        logger.info(
            "CUDA available: %s",
            torch.cuda.is_available(),
        )

        logger.info(
            "Device: %s",
            DEVICE,
        )

        # ----------------------------------------------------
        # GPU Information
        # ----------------------------------------------------

        if DEVICE.type == "cuda":

            try:

                logger.info(
                    "GPU: %s",
                    torch.cuda.get_device_name(0),
                )

                logger.info(
                    "GPU memory: %.2f GB",
                    (
                        torch.cuda
                        .get_device_properties(0)
                        .total_memory
                        / (1024 ** 3)
                    ),
                )

            except Exception as exc:

                logger.warning(
                    "Could not read GPU information: %s",
                    exc,
                )

        # ----------------------------------------------------
        # Model Information
        # ----------------------------------------------------

        logger.info(
            "Model: %s",
            MODEL_NAME,
        )

        logger.info(
            "BiRefNet revision: %s",
            BIREFNET_REVISION,
        )

        # ----------------------------------------------------
        # Hugging Face Authentication
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
        # Model Loading Arguments
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # Do NOT call from_pretrained() before these arguments
        # are completely configured.
        #
        # from_pretrained() must be called ONLY ONCE.
        #
        # ----------------------------------------------------

        model_kwargs = {
            "trust_remote_code": True,
            "revision": BIREFNET_REVISION,
        }

        # ----------------------------------------------------
        # Hugging Face Token
        # ----------------------------------------------------

        if HF_TOKEN:

            model_kwargs["token"] = HF_TOKEN

        # ----------------------------------------------------
        # Load Model
        # ----------------------------------------------------

        logger.info(
            "Loading BiRefNet from Hugging Face..."
        )

        logger.info(
            "Using pinned revision: %s",
            BIREFNET_REVISION,
        )

        try:

            self.model = (
                AutoModelForImageSegmentation.from_pretrained(
                    MODEL_NAME,
                    **model_kwargs,
                )
            )

        except Exception:

            logger.exception(
                "Failed to load BiRefNet model."
            )

            raise

        # ----------------------------------------------------
        # Move Model To Device
        # ----------------------------------------------------

        logger.info(
            "Moving BiRefNet to device: %s",
            DEVICE,
        )

        try:

            self.model = self.model.to(
                DEVICE
            )

        except Exception:

            logger.exception(
                "Failed to move BiRefNet to device: %s",
                DEVICE,
            )

            raise

        # ----------------------------------------------------
        # Evaluation Mode
        # ----------------------------------------------------

        self.model.eval()

        # ----------------------------------------------------
        # Detect Model Dtype
        # ----------------------------------------------------

        try:

            self.dtype = next(
                self.model.parameters()
            ).dtype

        except StopIteration:

            logger.warning(
                "Could not determine BiRefNet model dtype. "
                "Using float32."
            )

            self.dtype = torch.float32

        logger.info(
            "Model dtype: %s",
            self.dtype,
        )

        # ----------------------------------------------------
        # Final Status
        # ----------------------------------------------------

        logger.info(
            "BiRefNet loaded successfully."
        )

        logger.info(
            "BiRefNet device: %s",
            DEVICE,
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

        input_path = Path(
            input_path
        )

        output_path = Path(
            output_path
        )

        if not input_path.exists():

            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        logger.info(
            "Sending image to remote BiRefNet service: %s",
            self.remote_url,
        )

        # ----------------------------------------------------
        # Read Input
        # ----------------------------------------------------

        with input_path.open(
            "rb"
        ) as file_obj:

            file_bytes = file_obj.read()

        boundary = "----BiRefNetBoundary"

        # ----------------------------------------------------
        # Multipart Body
        # ----------------------------------------------------

        body = (
            b"--"
            + boundary.encode()
            + b"\r\n"
            + (
                b'Content-Disposition: form-data; '
                b'name="file"; filename="'
            )
            + input_path.name.encode()
            + b'"\r\n'
            + b"Content-Type: application/octet-stream\r\n\r\n"
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

        # ----------------------------------------------------
        # Send Request
        # ----------------------------------------------------

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

        except error.URLError as exc:

            raise RuntimeError(
                "Could not connect to remote BiRefNet service: "
                f"{exc}"
            ) from exc

        except TimeoutError as exc:

            raise RuntimeError(
                "Remote BiRefNet request timed out."
            ) from exc

        # ----------------------------------------------------
        # Output Directory
        # ----------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Direct PNG Response
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
        # JSON Response
        # ----------------------------------------------------

        try:

            data = json.loads(
                payload.decode(
                    "utf-8"
                )
            )

        except Exception as exc:

            raise RuntimeError(
                "Remote BiRefNet returned an unexpected "
                "non-JSON response."
            ) from exc

        # ----------------------------------------------------
        # JSON Image Response
        # ----------------------------------------------------

        if (
            isinstance(data, dict)
            and "image" in data
        ):

            image_data = data["image"]

            # ------------------------------------------------
            # Base64 image
            # ------------------------------------------------

            if isinstance(
                image_data,
                str,
            ):

                encoded_data = image_data

                # Handle data URLs:
                #
                # data:image/png;base64,XXXX
                #

                if "," in encoded_data:

                    prefix, possible_data = (
                        encoded_data.split(
                            ",",
                            1,
                        )
                    )

                    if (
                        "base64"
                        in prefix.lower()
                    ):

                        encoded_data = possible_data

                try:

                    decoded = base64.b64decode(
                        encoded_data,
                        validate=True,
                    )

                    output_path.write_bytes(
                        decoded
                    )

                except (
                    ValueError,
                    binascii.Error,
                ):

                    # Fallback for APIs that return
                    # raw image data as text.

                    output_path.write_bytes(
                        image_data.encode(
                            "utf-8"
                        )
                    )

            # ------------------------------------------------
            # Raw bytes
            # ------------------------------------------------

            elif isinstance(
                image_data,
                (
                    bytes,
                    bytearray,
                ),
            ):

                output_path.write_bytes(
                    image_data
                )

            else:

                raise RuntimeError(
                    "Remote BiRefNet returned an unsupported "
                    "'image' value."
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
            "Remote BiRefNet response was not an image: "
            f"{data}"
        )

    # ========================================================
    # Local Background Removal
    # ========================================================

    def _remove_background_local(
        self,
        input_path: Path,
        output_path: Path,
    ) -> dict:

        if self.model is None:

            raise RuntimeError(
                "BiRefNet model is not loaded."
            )

        logger.info(
            "Processing image: %s",
            input_path,
        )

        # ----------------------------------------------------
        # Load Image
        # ----------------------------------------------------

        try:

            image = Image.open(
                input_path
            ).convert("RGB")

        except Exception as exc:

            raise RuntimeError(
                f"Could not open image: {input_path}"
            ) from exc

        original_size = image.size

        # ----------------------------------------------------
        # Transform Image
        # ----------------------------------------------------

        tensor = transform(
            image
        )

        tensor = tensor.unsqueeze(
            0
        )

        tensor = tensor.to(
            device=DEVICE,
            dtype=self.dtype,
        )

        # ----------------------------------------------------
        # Model Inference
        # ----------------------------------------------------

        try:

            with torch.inference_mode():

                prediction = self.model(
                    tensor
                )

        except Exception:

            logger.exception(
                "BiRefNet inference failed."
            )

            raise

        # ----------------------------------------------------
        # Extract Prediction
        # ----------------------------------------------------

        prediction = _extract_prediction(
            prediction
        )

        # ----------------------------------------------------
        # Validate Prediction
        # ----------------------------------------------------

        if not isinstance(
            prediction,
            torch.Tensor,
        ):

            raise RuntimeError(
                "BiRefNet returned an unsupported "
                "prediction type: "
                f"{type(prediction)}"
            )

        # ----------------------------------------------------
        # Convert To Mask
        # ----------------------------------------------------

        prediction = prediction.float()

        prediction = prediction.sigmoid()

        prediction = prediction.squeeze()

        # ----------------------------------------------------
        # Validate Mask Shape
        # ----------------------------------------------------

        if prediction.ndim != 2:

            raise RuntimeError(
                "Unexpected BiRefNet mask shape: "
                f"{tuple(prediction.shape)}"
            )

        # ----------------------------------------------------
        # Convert Tensor To PIL
        # ----------------------------------------------------

        mask = transforms.ToPILImage()(
            prediction.cpu()
        )

        # ----------------------------------------------------
        # Restore Original Resolution
        # ----------------------------------------------------

        mask = mask.resize(
            original_size,
            Image.Resampling.LANCZOS,
        )

        # ----------------------------------------------------
        # Apply Alpha Channel
        # ----------------------------------------------------

        result = image.convert(
            "RGBA"
        )

        result.putalpha(
            mask
        )

        # ----------------------------------------------------
        # Create Output Directory
        # ----------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Save PNG
        # ----------------------------------------------------

        result.save(
            output_path,
            format="PNG",
        )

        logger.info(
            "Saved background-removed image: %s",
            output_path,
        )

        # ----------------------------------------------------
        # Release Temporary GPU Memory
        # ----------------------------------------------------

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

    # ========================================================
    # Main Background Removal
    # ========================================================

    def remove_background(
        self,
        input_path: str | Path,
        output_path: str | Path,
    ) -> dict:

        input_path = Path(
            input_path
        )

        output_path = Path(
            output_path
        )

        # ----------------------------------------------------
        # Validate Input
        # ----------------------------------------------------

        if not input_path.exists():

            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        # ----------------------------------------------------
        # Remote Mode
        # ----------------------------------------------------

        if self.use_remote:

            return self._remove_background_remote(
                input_path,
                output_path,
            )

        # ----------------------------------------------------
        # Local Mode
        # ----------------------------------------------------

        return self._remove_background_local(
            input_path,
            output_path,
        )


# ============================================================
# Global BiRefNet Service
# ============================================================

birefnet_service = BiRefNetService()