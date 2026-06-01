"""Placeholder scene image generation (no external APIs)."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import Settings
from app.models.schemas import Scene

logger = logging.getLogger(__name__)

PALETTES = [
    ((15, 23, 42), (30, 58, 138)),
    ((24, 24, 27), (63, 63, 70)),
    ((20, 83, 45), (6, 78, 59)),
    ((69, 10, 10), (127, 29, 29)),
    ((49, 46, 129), (91, 33, 182)),
    ((15, 118, 110), (14, 116, 144)),
]


def _color_from_text(text: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    digest = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
    idx = int(digest[:2], 16) % len(PALETTES)
    return PALETTES[idx]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_gradient(
    draw: ImageDraw.ImageDraw,
    size: tuple[int, int],
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    w, h = size
    for y in range(h):
        ratio = y / max(h - 1, 1)
        color = tuple(
            int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)
        )
        draw.line([(0, y), (w, y)], fill=color)


def generate_scene_visual(
    scene: Scene,
    output_path: Path,
    settings: Settings,
) -> str:
    """Generate a scene background image from visual_prompt."""
    width = settings.video_width
    height = settings.video_height
    top, bottom = _color_from_text(scene.visual_prompt)

    img = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw, (width, height), top, bottom)

    title_font = _load_font(56)
    sub_font = _load_font(28)

    label = f"Scene {scene.index + 1}"
    title = scene.title.strip()[:72]
    if title.lower().startswith("cinematic visual inspired by:"):
        title = title.split(":", 1)[-1].strip()[:72]

    draw.text((80, height // 2 - 40), label, fill=(148, 163, 184), font=sub_font)
    if title and title != label:
        draw.text((80, height // 2 + 8), title, fill=(248, 250, 252), font=title_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="JPEG", quality=settings.visual_jpeg_quality)
    logger.debug("Generated visual %s", output_path.name)
    return str(output_path)
