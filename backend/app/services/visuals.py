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
    """Generate a scene background image from visual_prompt (no external APIs)."""
    width = settings.video_width
    height = settings.video_height
    top, bottom = _color_from_text(scene.visual_prompt)

    img = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw, (width, height), top, bottom)

    title_font = _load_font(56)
    sub_font = _load_font(28)

    title = scene.title[:80]
    prompt = scene.visual_prompt[:120]

    draw.text((80, height // 2 - 80), title, fill=(248, 250, 252), font=title_font)
    draw.text((80, height // 2 + 10), prompt, fill=(203, 213, 225), font=sub_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="JPEG", quality=92)
    logger.debug("Generated visual %s", output_path.name)
    return str(output_path)


def attach_visuals(
    scenes: list[Scene],
    visuals_dir: Path,
    settings: Settings,
) -> list[Scene]:
    updated: list[Scene] = []
    for scene in scenes:
        out = visuals_dir / f"scene_{scene.index:03d}.jpg"
        path = generate_scene_visual(scene, out, settings)
        updated.append(scene.model_copy(update={"image_path": path}))
    logger.info("Attached visuals for %d scenes", len(updated))
    return updated
