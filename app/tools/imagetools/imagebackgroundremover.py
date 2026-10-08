from pathlib import Path

from app.birefnet import birefnet_service


def remove_background(input_path: str | Path, output_path: str | Path) -> dict:
    return birefnet_service.remove_background(input_path, output_path)
