from typing import Any, Callable, Awaitable

from app.tools.pdf import operations as pdf_ops

# Registry mapping tool slug -> processor function
PROCESSORS: dict[str, Callable[..., Any]] = {
    "merge-pdf": pdf_ops.merge_pdfs,
    "split-pdf": pdf_ops.split_pdf,
    "compress-pdf": pdf_ops.compress_pdf,
    "pdf-to-jpg": pdf_ops.pdf_to_jpg,
    "jpg-to-pdf": pdf_ops.images_to_pdf,
    "compress-image": pdf_ops.compress_image,
}


def get_processor(slug: str):
    return PROCESSORS.get(slug)
