"""Lightweight media preprocessing before normalization."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageOps

from app.models.schemas import MediaType
from app.services.visual_assembly.assets import ValidatedAsset

logger = logging.getLogger(__name__)


def preprocess_image(asset: ValidatedAsset, work_dir: Path) -> Path:
    """
    Prepare an image for normalization: EXIF orientation, RGB, no alpha surprises.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    out = work_dir / f"pre_{asset.path.stem}.png"

    with Image.open(asset.path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (0, 0, 0))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(out, format="PNG")

    logger.debug("Preprocessed image %s -> %s", asset.path.name, out.name)
    return out


def preprocess_media(asset: ValidatedAsset, work_dir: Path) -> Path:
    """Return path ready for render normalization."""
    if asset.media_type == MediaType.IMAGE:
        return preprocess_image(asset, work_dir)
    return asset.path
