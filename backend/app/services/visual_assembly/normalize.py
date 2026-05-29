"""Rendering-safe media normalization (fixed frame size, consistent codecs)."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from app.config import Settings
from app.models.schemas import MediaType
from app.services.visual_assembly.assets import ValidatedAsset

logger = logging.getLogger(__name__)


def _fit_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale and center-crop to exact output dimensions."""
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = max(int(src_w * scale), 1)
    new_h = max(int(src_h * scale), 1)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def normalize_image_for_render(
    source: Path,
    output: Path,
    settings: Settings,
) -> Path:
    """Write a JPEG at the configured video resolution."""
    output.parent.mkdir(parents=True, exist_ok=True)
    target = (settings.video_width, settings.video_height)

    with Image.open(source) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        frame = _fit_cover(img, target[0], target[1])
        frame.save(output, format="JPEG", quality=settings.visual_jpeg_quality)

    logger.debug("Normalized image -> %s (%dx%d)", output.name, target[0], target[1])
    return output


def normalize_for_render(
    asset: ValidatedAsset,
    preprocessed: Path,
    output_dir: Path,
    settings: Settings,
) -> tuple[Path, MediaType]:
    """
    Produce render-ready media paths.

    Images are written as normalized JPEGs. Videos are validated in place;
    resize/trim happens at render time via MoviePy for consistency with scene duration.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if asset.media_type == MediaType.IMAGE:
        out = output_dir / f"scene_{asset.path.stem}_norm.jpg"
        normalize_image_for_render(preprocessed, out, settings)
        return out, MediaType.IMAGE

    return asset.path, MediaType.VIDEO
