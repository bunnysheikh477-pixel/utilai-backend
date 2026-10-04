from __future__ import annotations

import io
import os
import uuid
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader, PdfWriter

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - optional dependency
    fitz = None


def _require_fitz() -> None:
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF is required for this PDF operation. Install it with: pip install PyMuPDF"
        )


# -----------------------------
# Helpers
# -----------------------------


def _safe_path(path: str) -> str:
    if not path:
        raise ValueError("PDF path is required.")

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF.")

    return str(file_path)


def _page_index(page_number: int) -> int:
    page_number = int(page_number)

    if page_number < 1:
        raise ValueError("page_number must start at 1.")

    return page_number - 1


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    if not color:
        return 0.0, 0.0, 0.0

    color = color.strip().lstrip("#")

    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)

    if len(color) != 6:
        return 0.0, 0.0, 0.0

    try:
        r = int(color[0:2], 16) / 255
        g = int(color[2:4], 16) / 255
        b = int(color[4:6], 16) / 255
        return r, g, b
    except ValueError:
        return 0.0, 0.0, 0.0


def _output_path(output: str) -> str:
    output_path = Path(output)

    if output_path.suffix.lower() != ".pdf":
        output_path = output_path.with_suffix(".pdf")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    return str(output_path)


def _rect(x: float, y: float, width: float, height: float) -> "fitz.Rect":
    return fitz.Rect(float(x), float(y), float(x) + float(width), float(y) + float(height))


# -----------------------------
# Merge / Split / Compress (pypdf + PIL)
# -----------------------------


def merge_pdfs(paths: list[str], output: str) -> dict[str, Any]:
    writer = PdfWriter()

    for path in paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    with open(output, "wb") as f:
        writer.write(f)

    return {"success": True, "pages": len(writer.pages), "output": output}


def split_pdf(path: str, output_dir: str) -> list[str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(path)
    outputs: list[str] = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        out = output_path / f"page_{i + 1}.pdf"
        with open(out, "wb") as f:
            writer.write(f)
        outputs.append(str(out))

    return outputs


def compress_pdf(path: str, output: str) -> dict[str, Any]:
    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        try:
            page.compress_content_streams()
        except Exception:
            pass
        writer.add_page(page)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    with open(output, "wb") as f:
        writer.write(f)

    return {"success": True, "output": output}


def images_to_pdf(image_paths: list[str], output: str) -> dict[str, Any]:
    if not image_paths:
        raise ValueError("No images provided.")

    images = []

    try:
        for path in image_paths:
            image = Image.open(path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            images.append(image)

        Path(output).parent.mkdir(parents=True, exist_ok=True)

        images[0].save(output, "PDF", save_all=True, append_images=images[1:])

    finally:
        for image in images:
            try:
                image.close()
            except Exception:
                pass

    return {"success": True, "output": output, "pages": len(images)}


def jpg_to_pdf(image_paths: list[str], output: str) -> dict[str, Any]:
    return images_to_pdf(image_paths, output)


def compress_image(path: str, output: str, quality: int = 80) -> dict[str, Any]:
    if not 1 <= quality <= 100:
        raise ValueError("Quality must be between 1 and 100.")

    image = Image.open(path)

    try:
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(output, "JPEG", optimize=True, quality=quality)
    finally:
        image.close()

    return {"success": True, "output": output, "quality": quality}


# -----------------------------
# PyMuPDF-powered operations (editing, export, info)
# -----------------------------


def pdf_to_jpg(path: str, output_dir: str, dpi: int = 150) -> list[str]:
    _require_fitz()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document = fitz.open(path)
    outputs: list[str] = []

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    try:
        for i, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            out = output_path / f"page_{i + 1}.jpg"
            pixmap.save(str(out))
            outputs.append(str(out))
    finally:
        document.close()

    return outputs


def pdf_info(path: str) -> dict[str, Any]:
    path = _safe_path(path)
    _require_fitz()

    document = fitz.open(path)

    try:
        pages = []
        for index in range(document.page_count):
            page = document.load_page(index)
            rect = page.rect
            pages.append({"page_number": index + 1, "width": rect.width, "height": rect.height})

        return {"success": True, "pages": document.page_count, "metadata": document.metadata, "page_sizes": pages}
    finally:
        document.close()


def rotate_pdf_page(path: str, page_number: int, angle: int, output: str = "edited.pdf") -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        angle = int(angle)
        if angle % 90 != 0:
            raise ValueError("Rotation angle must be a multiple of 90.")
        page = document.load_page(index)
        current_rotation = page.rotation
        page.set_rotation((current_rotation + angle) % 360)
        document.save(output)
        return {"success": True, "action": "rotate", "page_number": page_number, "angle": angle, "output": output}
    finally:
        document.close()


def delete_pdf_page(path: str, page_number: int, output: str = "edited.pdf") -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        if document.page_count <= 1:
            raise ValueError("A PDF must contain at least one page.")
        document.delete_page(index)
        document.save(output)
        return {"success": True, "action": "delete", "page_number": page_number, "output": output}
    finally:
        document.close()


def extract_pdf_pages(path: str, start_page: int, end_page: int, output: str = "edited.pdf") -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        start = _page_index(start_page)
        end = _page_index(end_page)
        if start < 0 or end >= document.page_count:
            raise ValueError("Page range is outside the PDF.")
        if start > end:
            raise ValueError("start_page must be <= end_page.")
        new_document = fitz.open()
        try:
            new_document.insert_pdf(document, from_page=start, to_page=end)
            new_document.save(output)
        finally:
            new_document.close()
        return {"success": True, "action": "extract", "start_page": start_page, "end_page": end_page, "output": output}
    finally:
        document.close()


def add_text_to_pdf(path: str, page_number: int, text: str, x: float = 72, y: float = 72, font_size: float = 14, output: str = "edited.pdf", color: str = "#000000", font_name: str = "helv", width: float = 300, height: float = 100) -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        page = document.load_page(index)
        rectangle = _rect(x, y, width, height)
        rgb = _hex_to_rgb(color)
        page.insert_textbox(rectangle, str(text), fontsize=float(font_size), fontname=font_name, color=rgb, overlay=True)
        document.save(output)
        return {"success": True, "action": "text", "page_number": page_number, "text": text, "output": output}
    finally:
        document.close()


def add_watermark(path: str, text: str, output: str = "edited.pdf", font_size: float = 40, color: str = "#888888") -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        rgb = _hex_to_rgb(color)
        for page in document:
            rectangle = page.rect
            page.insert_text((rectangle.width / 2, rectangle.height / 2), text, fontsize=float(font_size), fontname="helv", color=rgb, rotate=45, overlay=True)
        document.save(output)
        return {"success": True, "action": "watermark", "text": text, "output": output}
    finally:
        document.close()


def add_image_to_pdf(path: str, page_number: int, image_path: str, x: float = 72, y: float = 72, width: float = 200, height: float = 200, output: str = "edited.pdf", rotation: float = 0) -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        page = document.load_page(index)
        rectangle = _rect(x, y, width, height)
        page.insert_image(rectangle, filename=str(image_file), overlay=True)
        document.save(output)
        return {"success": True, "action": "image", "page_number": page_number, "output": output}
    finally:
        document.close()


def add_rectangle_to_pdf(path: str, page_number: int, x: float, y: float, width: float, height: float, output: str = "edited.pdf", fill: str | None = None, stroke: str = "#000000", stroke_width: float = 1, opacity: float = 1.0) -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        page = document.load_page(index)
        rectangle = _rect(x, y, width, height)
        fill_rgb = None
        if fill:
            fill_rgb = _hex_to_rgb(fill)
        stroke_rgb = _hex_to_rgb(stroke)
        page.draw_rect(rectangle, color=stroke_rgb, fill=fill_rgb if fill else None, width=float(stroke_width), overlay=True, fill_opacity=max(0.0, min(1.0, float(opacity))), stroke_opacity=max(0.0, min(1.0, float(opacity))))
        document.save(output)
        return {"success": True, "action": "rectangle", "page_number": page_number, "output": output}
    finally:
        document.close()


def add_line_to_pdf(path: str, page_number: int, x1: float, y1: float, x2: float, y2: float, output: str = "edited.pdf", stroke: str = "#000000", stroke_width: float = 1) -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        page = document.load_page(index)
        page.draw_line(fitz.Point(float(x1), float(y1)), fitz.Point(float(x2), float(y2)), color=_hex_to_rgb(stroke), width=float(stroke_width), overlay=True)
        document.save(output)
        return {"success": True, "action": "line", "page_number": page_number, "output": output}
    finally:
        document.close()


def extract_page_text(path: str, page_number: int) -> dict[str, Any]:
    path = _safe_path(path)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        page = document.load_page(index)
        data = page.get_text("dict")
        objects: list[dict[str, Any]] = []

        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span.get("bbox")
                    if not bbox:
                        continue
                    x0, y0, x1, y1 = bbox
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    objects.append({
                        "id": f"pdf-text-{uuid.uuid4().hex}",
                        "type": "text",
                        "page": page_number,
                        "x": x0,
                        "y": y0,
                        "width": x1 - x0,
                        "height": y1 - y0,
                        "rotation": 0,
                        "opacity": 1,
                        "text": text,
                        "originalText": text,
                        "originalX": x0,
                        "originalY": y0,
                        "originalWidth": x1 - x0,
                        "originalHeight": y1 - y0,
                        "fontSize": span.get("size", 12),
                        "fontFamily": span.get("font", "Helvetica"),
                        "color": "#000000",
                        "fontWeight": "normal",
                        "fontStyle": "normal",
                        "textAlign": "left",
                        "lineHeight": 1.2,
                        "letterSpacing": 0,
                        "underline": False,
                        "backgroundColor": "transparent",
                        "isExisting": True,
                    })

        return {"success": True, "page_number": page_number, "objects": objects}
    finally:
        document.close()


def replace_text_in_pdf(path: str, page_number: int, old_text: str, new_text: str, x: float, y: float, width: float, height: float, font_size: float = 12, color: str = "#000000", output: str = "edited.pdf") -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        index = _page_index(page_number)
        if index >= document.page_count:
            raise ValueError("Page number is outside the PDF.")
        page = document.load_page(index)
        matches = page.search_for(old_text)
        target = None
        requested_rect = _rect(x, y, width, height)
        if matches:
            target = min(matches, key=lambda rect: (abs(rect.x0 - requested_rect.x0) + abs(rect.y0 - requested_rect.y0)))
        if target is None:
            raise ValueError(f"Could not find existing text: {old_text}")
        page.add_redact_annot(target, fill=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_REMOVE)
        page.insert_textbox(target, new_text, fontsize=float(font_size), fontname="helv", color=_hex_to_rgb(color), overlay=True)
        document.save(output)
        return {"success": True, "action": "replace_text", "page_number": page_number, "old_text": old_text, "new_text": new_text, "output": output}
    finally:
        document.close()


def export_editor_objects(path: str, objects: list[dict[str, Any]], output: str = "edited.pdf") -> dict[str, Any]:
    path = _safe_path(path)
    output = _output_path(output)
    _require_fitz()

    document = fitz.open(path)

    try:
        for obj in objects:
            object_type = obj.get("type")
            page_number = int(obj.get("page", 1))
            index = _page_index(page_number)
            if index >= document.page_count:
                continue
            page = document.load_page(index)
            x = float(obj.get("x", 0))
            y = float(obj.get("y", 0))
            width = float(obj.get("width", 100))
            height = float(obj.get("height", 50))

            if object_type == "text":
                is_existing = bool(obj.get("isExisting", False))
                original_text = obj.get("originalText")
                current_text = obj.get("text", "")

                if is_existing and original_text and current_text != original_text:
                    matches = page.search_for(str(original_text))
                    if matches:
                        target = min(matches, key=lambda rect: (abs(rect.x0 - x) + abs(rect.y0 - y)))
                        page.add_redact_annot(target, fill=False)
                        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_REMOVE)
                        page.insert_textbox(_rect(x, y, width, height), str(current_text), fontsize=float(obj.get("fontSize", 12)), fontname="helv", color=_hex_to_rgb(obj.get("color", "#000000")), overlay=True)

                elif not is_existing:
                    page.insert_textbox(_rect(x, y, width, height), str(current_text), fontsize=float(obj.get("fontSize", 12)), fontname="helv", color=_hex_to_rgb(obj.get("color", "#000000")), overlay=True)

            elif object_type == "rectangle":
                page.draw_rect(_rect(x, y, width, height), color=_hex_to_rgb(obj.get("stroke", "#000000")), fill=_hex_to_rgb(obj.get("fill", "#ffffff")) if obj.get("fill") else None, width=float(obj.get("strokeWidth", 1)), overlay=True)

            elif object_type == "circle":
                rect = _rect(x, y, width, height)
                page.draw_oval(rect, color=_hex_to_rgb(obj.get("stroke", "#000000")), fill=_hex_to_rgb(obj.get("fill", "#ffffff")) if obj.get("fill") else None, width=float(obj.get("strokeWidth", 1)), overlay=True)

            elif object_type == "line":
                page.draw_line(fitz.Point(x, y), fitz.Point(float(obj.get("x2", x + width)), float(obj.get("y2", y + height))), color=_hex_to_rgb(obj.get("stroke", "#000000")), width=float(obj.get("strokeWidth", 1)), overlay=True)

            elif object_type == "highlight":
                page.draw_rect(_rect(x, y, width, height), fill=_hex_to_rgb(obj.get("fill", "#ffff00")), color=None, fill_opacity=float(obj.get("opacity", 0.35)), overlay=True)

            elif object_type == "draw":
                points = obj.get("points", [])
                if len(points) >= 2:
                    for first, second in zip(points, points[1:]):
                        page.draw_line(fitz.Point(float(first["x"]), float(first["y"])), fitz.Point(float(second["x"]), float(second["y"])), color=_hex_to_rgb(obj.get("stroke", "#000000")), width=float(obj.get("strokeWidth", 2)), overlay=True)

        document.save(output)
        return {"success": True, "action": "export", "objects_processed": len(objects), "output": output}
    finally:
        document.close()


# Dispatcher

def edit_pdf(path: str, action: str, output: str = "edited.pdf", **kwargs: Any) -> dict[str, Any]:
    name = (action or "").strip().lower()

    if name in {"info", "pdf-info"}:
        return pdf_info(path)

    if name == "rotate":
        return rotate_pdf_page(path, kwargs["page_number"], kwargs["angle"], output)

    if name == "delete":
        return delete_pdf_page(path, kwargs["page_number"], output)

    if name == "extract":
        return extract_pdf_pages(path, kwargs["start_page"], kwargs["end_page"], output)

    if name == "text":
        return add_text_to_pdf(path, kwargs["page_number"], kwargs["text"], kwargs.get("x", 72), kwargs.get("y", 72), kwargs.get("font_size", 14), output, kwargs.get("color", "#000000"), kwargs.get("font_name", "helv"), kwargs.get("width", 300), kwargs.get("height", 100))

    if name in {"replace-text", "replace_text", "edit-text", "edit_text"}:
        return replace_text_in_pdf(path=path, page_number=kwargs["page_number"], old_text=kwargs["old_text"], new_text=kwargs["new_text"], x=kwargs["x"], y=kwargs["y"], width=kwargs["width"], height=kwargs["height"], font_size=kwargs.get("font_size", 12), color=kwargs.get("color", "#000000"), output=output)

    if name in {"extract-text", "extract_text"}:
        return extract_page_text(path, kwargs["page_number"])

    if name == "watermark":
        return add_watermark(path, kwargs["text"], output, kwargs.get("font_size", 40), kwargs.get("color", "#888888"))

    if name == "image":
        return add_image_to_pdf(path, kwargs["page_number"], kwargs["image_path"], kwargs.get("x", 72), kwargs.get("y", 72), kwargs.get("width", 200), kwargs.get("height", 200), output, kwargs.get("rotation", 0))

    if name in {"rect", "rectangle"}:
        return add_rectangle_to_pdf(path, kwargs["page_number"], kwargs["x"], kwargs["y"], kwargs["width"], kwargs["height"], output, kwargs.get("fill", None), kwargs.get("stroke", "#000000"), kwargs.get("stroke_width", 1), kwargs.get("opacity", 1.0))

    if name == "line":
        return add_line_to_pdf(path, kwargs["page_number"], kwargs["x1"], kwargs["y1"], kwargs["x2"], kwargs["y2"], output, kwargs.get("stroke", "#000000"), kwargs.get("stroke_width", 1))

    if name in {"export", "save", "export-editor", "export_editor"}:
        return export_editor_objects(path=path, objects=kwargs.get("objects", []), output=output)

    raise ValueError(f"Unknown PDF editor action: {action}")


PDF_TOOLS = {
    "merge-pdf": merge_pdfs,
    "split-pdf": split_pdf,
    "compress-pdf": compress_pdf,
    "pdf-to-jpg": pdf_to_jpg,
    "images-to-pdf": images_to_pdf,
    "jpg-to-pdf": jpg_to_pdf,
    "compress-image": compress_image,
    "pdf-info": pdf_info,
    "rotate-pdf-page": rotate_pdf_page,
    "delete-pdf-page": delete_pdf_page,
    "add-text-to-pdf": add_text_to_pdf,
    "add-rectangle-to-pdf": add_rectangle_to_pdf,
    "add-line-to-pdf": add_line_to_pdf,
    "add-image-to-pdf": add_image_to_pdf,
    "add-watermark": add_watermark,
    "extract-pdf-pages": extract_pdf_pages,
    "pdf-editor": edit_pdf,
}
