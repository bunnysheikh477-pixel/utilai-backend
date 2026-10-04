
import os
import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "ZhengPeng7/BiRefNet"

INPUT_DIR = "input"
OUTPUT_DIR = "output"

INPUT_IMAGE = os.path.join(INPUT_DIR, "test.jpeg")
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, "background_removed.png")


# ============================================================
# DEVICE
# ============================================================

if torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

print("=" * 60)
print("BiRefNet Background Remover")
print("=" * 60)

print(f"Device: {DEVICE}")


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading BiRefNet model...")
print("First run may take some time because model weights are downloaded.")

model = AutoModelForImageSegmentation.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)

model = model.float()
model.to(DEVICE)
model.eval()

print("BiRefNet loaded successfully.")


# ============================================================
# IMAGE TRANSFORMATION
# ============================================================

IMAGE_SIZE = (1024, 1024)

transform_image = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    ),
])


# ============================================================
# BACKGROUND REMOVAL FUNCTION
# ============================================================

def remove_background(input_path, output_path):

    print("\nOpening image:")
    print(input_path)

    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    image = Image.open(input_path).convert("RGB")

    original_size = image.size

    print(f"Original size: {original_size}")

    # --------------------------------------------------------
    # Prepare image
    # --------------------------------------------------------

    input_tensor = transform_image(image)

    input_tensor = input_tensor.unsqueeze(0)
    input_tensor = input_tensor.float()
    input_tensor = input_tensor.to(DEVICE)

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    print("Running BiRefNet...")

    with torch.no_grad():

        prediction = model(input_tensor)[-1]

        prediction = prediction.sigmoid()

    # --------------------------------------------------------
    # Convert prediction to mask
    # --------------------------------------------------------

    prediction = prediction.cpu()

    prediction = prediction[0]

    prediction = prediction.squeeze()

    mask = transforms.ToPILImage()(prediction)

    # --------------------------------------------------------
    # Resize mask back to original image size
    # --------------------------------------------------------

    mask = mask.resize(
        original_size,
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # Create transparent image
    # --------------------------------------------------------

    image = image.convert("RGBA")

    image.putalpha(mask)

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save PNG
    # --------------------------------------------------------

    image.save(
        output_path,
        format="PNG"
    )

    print("\nBackground removed successfully.")

    print(f"Output: {output_path}")

    print(f"Output size: {image.size}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # Make sure folders exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Check input image
    if not os.path.exists(INPUT_IMAGE):

        print("\nERROR:")
        print(f"Image not found: {INPUT_IMAGE}")

        print("\nPut your image here:")

        print(
            os.path.abspath(INPUT_IMAGE)
        )

        print(
            "\nThen rename it to: test.jpg"
        )

        raise SystemExit(1)

    # Run background removal
    remove_background(
        INPUT_IMAGE,
        OUTPUT_IMAGE
    )

    print("\nDone!")





# from __future__ import annotations

# import logging
# from pathlib import Path
# from typing import Union

# import torch
# from PIL import Image
# from torchvision import transforms
# from transformers import AutoModelForImageSegmentation

# logger = logging.getLogger(__name__)

# MODEL_NAME = "ZhengPeng7/BiRefNet"

# IMAGE_SIZE = (1024, 1024)

# NORMALIZE_MEAN = [0.485, 0.456, 0.406]
# NORMALIZE_STD = [0.229, 0.224, 0.225]


# # ============================================================
# # DEVICE
# # ============================================================

# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# # ============================================================
# # IMAGE TRANSFORM
# # ============================================================

# transform_image = transforms.Compose(
#     [
#         transforms.Resize(IMAGE_SIZE),
#         transforms.ToTensor(),
#         transforms.Normalize(
#             NORMALIZE_MEAN,
#             NORMALIZE_STD,
#         ),
#     ]
# )


# # ============================================================
# # MODEL LOADING
# # ============================================================

# logger.info("=" * 60)
# logger.info("Loading BiRefNet Background Remover")
# logger.info("=" * 60)
# logger.info("Device: %s", DEVICE)
# logger.info("Model: %s", MODEL_NAME)


# try:
#     model = AutoModelForImageSegmentation.from_pretrained(
#         MODEL_NAME,
#         trust_remote_code=True,
#     )

#     model = model.to(DEVICE)
#     model.eval()

#     logger.info("BiRefNet loaded successfully.")

# except Exception:
#     logger.exception("Failed to load BiRefNet model.")
#     raise


# # ============================================================
# # GET MODEL DTYPE
# # ============================================================

# def _get_model_dtype() -> torch.dtype:
#     """
#     Get the dtype of the first model parameter.

#     This prevents errors such as:

#     RuntimeError:
#     Input type (float) and bias type (struct c10::Half)
#     should be the same
#     """

#     try:
#         return next(model.parameters()).dtype
#     except StopIteration:
#         return torch.float32


# # ============================================================
# # BACKGROUND REMOVER
# # ============================================================

# def remove_background(
#     input_path: Union[str, Path],
#     output_path: Union[str, Path],
# ) -> dict:
#     """
#     Remove the background from an image using BiRefNet.

#     Args:
#         input_path:
#             Path to uploaded image.

#         output_path:
#             Path where transparent PNG should be saved.

#     Returns:
#         Dictionary containing output path and image information.
#     """

#     input_path = Path(input_path)
#     output_path = Path(output_path)

#     if not input_path.exists():
#         raise FileNotFoundError(
#             f"Input image not found: {input_path}"
#         )

#     logger.info("Processing image: %s", input_path)

#     # --------------------------------------------------------
#     # OPEN IMAGE
#     # --------------------------------------------------------

#     image = Image.open(input_path).convert("RGB")

#     original_size = image.size

#     logger.info("Original image size: %s", original_size)

#     # --------------------------------------------------------
#     # PREPARE INPUT
#     # --------------------------------------------------------

#     input_tensor = transform_image(image)

#     input_tensor = input_tensor.unsqueeze(0)

#     # --------------------------------------------------------
#     # MATCH MODEL DTYPE
#     # --------------------------------------------------------

#     model_dtype = _get_model_dtype()

#     input_tensor = input_tensor.to(
#         device=DEVICE,
#         dtype=model_dtype,
#     )

#     logger.info("Model dtype: %s", model_dtype)
#     logger.info("Input dtype: %s", input_tensor.dtype)

#     # --------------------------------------------------------
#     # MODEL INFERENCE
#     # --------------------------------------------------------

#     logger.info("Running BiRefNet inference...")

#     with torch.inference_mode():
#         prediction = model(input_tensor)

#         # BiRefNet usually returns multiple outputs.
#         # The final output is the segmentation prediction.
#         if isinstance(prediction, (tuple, list)):
#             prediction = prediction[-1]

#         elif hasattr(prediction, "logits"):
#             prediction = prediction.logits

#     # --------------------------------------------------------
#     # SIGMOID
#     # --------------------------------------------------------

#     prediction = prediction.float().sigmoid()

#     # --------------------------------------------------------
#     # REMOVE BATCH / CHANNEL DIMENSIONS
#     # --------------------------------------------------------

#     prediction = prediction.squeeze()

#     # --------------------------------------------------------
#     # CONVERT MASK TO PIL
#     # --------------------------------------------------------

#     mask = transforms.ToPILImage()(prediction.cpu())

#     mask = mask.resize(
#         original_size,
#         Image.Resampling.LANCZOS,
#     )

#     # --------------------------------------------------------
#     # CREATE TRANSPARENT IMAGE
#     # --------------------------------------------------------

#     result_image = image.convert("RGBA")

#     result_image.putalpha(mask)

#     # --------------------------------------------------------
#     # CREATE OUTPUT DIRECTORY
#     # --------------------------------------------------------

#     output_path.parent.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     # --------------------------------------------------------
#     # SAVE PNG
#     # --------------------------------------------------------

#     result_image.save(
#         output_path,
#         format="PNG",
#     )

#     logger.info(
#         "Background removed successfully: %s",
#         output_path,
#     )

#     return {
#         "output": str(output_path),
#         "filename": output_path.name,
#         "width": original_size[0],
#         "height": original_size[1],
#     }


# # ============================================================
# # STANDALONE TEST
# # ============================================================

# if __name__ == "__main__":

#     input_dir = Path("input")
#     output_dir = Path("output")

#     input_dir.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     output_dir.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     input_image = input_dir / "test.jpg"
#     output_image = output_dir / "background_removed.png"

#     if not input_image.exists():

#         print()
#         print("ERROR: Input image not found.")
#         print()
#         print(f"Put your image here:")
#         print(input_image.resolve())
#         print()

#         raise SystemExit(1)

#     result = remove_background(
#         input_image,
#         output_image,
#     )

#     print()
#     print("=" * 60)
#     print("BACKGROUND REMOVAL COMPLETE")
#     print("=" * 60)
#     print(f"Output: {result['output']}")
#     print(f"Size: {result['width']} x {result['height']}")