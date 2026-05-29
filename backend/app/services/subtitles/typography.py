"""Typography helpers — font resolution and responsive text layout."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import ImageFont

from app.services.subtitles.config import ResolvedSubtitleStyle

logger = logging.getLogger(__name__)

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttf",
]


def resolve_font_path(explicit: str | None = None) -> str | None:
    if explicit and Path(explicit).exists():
        return explicit
    for candidate in _FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def load_font(style: ResolvedSubtitleStyle) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = resolve_font_path(style.font_path)
    if path:
        try:
            return ImageFont.truetype(path, style.font_size)
        except OSError as exc:
            logger.warning("Failed to load font %s: %s", path, exc)
    return ImageFont.load_default()


def wrap_text_to_width(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current: list[str] = []

    for word in words:
        trial = " ".join(current + [word]) if current else word
        bbox = font.getbbox(trial)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines


def measure_text_block(
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_spacing: int,
) -> tuple[int, int]:
    if not lines:
        return 0, 0

    max_w = 0
    total_h = 0
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += h
        if i < len(lines) - 1:
            total_h += line_spacing

    return max_w, total_h
