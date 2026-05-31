"""Rendering helpers — color conversion and subtitle image rasterization."""

from __future__ import annotations

import logging

import numpy as np
from PIL import Image, ImageDraw

from app.services.subtitles.config import ResolvedSubtitleStyle
from app.services.subtitles.typography import (
    load_font,
    measure_text_block,
    wrap_text_to_width,
)
from app.services.subtitles.utils import sanitize_display_text

logger = logging.getLogger(__name__)


def hex_to_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return (r, g, b, alpha)


def render_subtitle_rgba(
    text: str,
    style: ResolvedSubtitleStyle,
) -> np.ndarray:
    """
    Rasterize subtitle text to an RGBA numpy array (lightweight Pillow path).

    Supports stroke, optional background box, and responsive wrapping.
    """
    font = load_font(style)
    display_text = sanitize_display_text(text)
    lines = wrap_text_to_width(display_text, font, style.max_text_width, max_lines=2)
    if not lines:
        return np.zeros((1, 1, 4), dtype=np.uint8)

    text_w, text_h = measure_text_block(lines, font, style.line_spacing)
    pad = style.background_padding + style.stroke_width
    img_w = text_w + pad * 2
    img_h = text_h + pad * 2

    image = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if style.background_color and style.background_opacity > 0:
        bg_alpha = int(max(0, min(1.0, style.background_opacity)) * 255)
        bg_rgba = hex_to_rgba(style.background_color, bg_alpha)
        rect = [(0, 0), (img_w - 1, img_h - 1)]
        radius = max(4, style.background_padding // 2)
        if hasattr(draw, "rounded_rectangle"):
            draw.rounded_rectangle(rect, radius=radius, fill=bg_rgba)
        else:
            draw.rectangle(rect, fill=bg_rgba)

    fill = hex_to_rgba(style.text_color)
    stroke = hex_to_rgba(style.stroke_color)
    stroke_w = style.stroke_width

    y = pad
    for line in lines:
        bbox = font.getbbox(line)
        line_h = bbox[3] - bbox[1]
        x = (img_w - (bbox[2] - bbox[0])) // 2

        if stroke_w > 0:
            for dx in range(-stroke_w, stroke_w + 1):
                for dy in range(-stroke_w, stroke_w + 1):
                    if dx * dx + dy * dy <= stroke_w * stroke_w:
                        draw.text((x + dx, y + dy), line, font=font, fill=stroke)

        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + style.line_spacing

    return np.array(image)


def compute_overlay_position(
    style: ResolvedSubtitleStyle,
    overlay_width: int,
    overlay_height: int,
) -> tuple[str, int]:
    """
    Return MoviePy position spec (horizontal, vertical pixel from top).

    Horizontal is always centered via 'center'.
    """
    vw, vh = style.video_width, style.video_height
    position = style.position.lower().strip()

    if position == "center":
        y = (vh - overlay_height) // 2
    elif position == "lower_third":
        y = int(vh * 0.68) - overlay_height
    else:
        y = vh - style.margin_y - overlay_height

    y = max(style.margin_y, min(y, vh - overlay_height - style.margin_y))
    return ("center", y)
