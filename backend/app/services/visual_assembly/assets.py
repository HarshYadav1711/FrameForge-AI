"""Media asset validation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import Settings
from app.core.exceptions import VisualAssemblyError
from app.models.schemas import MediaType
from app.services.visual_assembly.types import IMAGE_EXTENSIONS, MEDIA_EXTENSIONS, VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidatedAsset:
    path: Path
    media_type: MediaType
    size_bytes: int
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None


def _probe_image(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        img.verify()
    with Image.open(path) as img:
        return img.size


def _probe_video(path: Path) -> tuple[int, int, float]:
    from app.services.subtitles.moviepy_compat import import_video_file_clip

    VideoFileClip = import_video_file_clip()
    clip = VideoFileClip(str(path))
    try:
        w, h = clip.size
        duration = float(clip.duration or 0.0)
        if duration <= 0:
            raise VisualAssemblyError(f"Video has no duration: {path.name}")
        return int(w), int(h), duration
    finally:
        clip.close()


def media_type_for_path(path: Path) -> MediaType | None:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    if ext in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    return None


def validate_media_asset(path: Path, settings: Settings) -> ValidatedAsset:
    """Validate a media file before preprocessing."""
    if not path.exists():
        raise VisualAssemblyError(f"Media file not found: {path}")
    if not path.is_file():
        raise VisualAssemblyError(f"Not a file: {path}")

    ext = path.suffix.lower()
    if ext not in MEDIA_EXTENSIONS:
        raise VisualAssemblyError(
            f"Unsupported media extension '{ext}' (allowed: {', '.join(sorted(MEDIA_EXTENSIONS))})"
        )

    size_bytes = path.stat().st_size
    if size_bytes > settings.visual_max_asset_bytes:
        raise VisualAssemblyError(
            f"Media file too large ({size_bytes} bytes, max {settings.visual_max_asset_bytes})"
        )
    if size_bytes == 0:
        raise VisualAssemblyError(f"Media file is empty: {path.name}")

    media_type = media_type_for_path(path)
    assert media_type is not None

    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None

    try:
        if media_type == MediaType.IMAGE:
            width, height = _probe_image(path)
        else:
            width, height, duration_seconds = _probe_video(path)
    except UnidentifiedImageError as exc:
        raise VisualAssemblyError(f"Invalid image file: {path.name}") from exc
    except VisualAssemblyError:
        raise
    except Exception as exc:
        raise VisualAssemblyError(f"Could not read media: {path.name}") from exc

    logger.debug(
        "Validated %s (%s, %sx%s)",
        path.name,
        media_type.value,
        width,
        height,
    )
    return ValidatedAsset(
        path=path,
        media_type=media_type,
        size_bytes=size_bytes,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )


def find_scene_media(visuals_dir: Path, scene_index: int) -> Path | None:
    """Locate user-provided media named scene_NNN.<ext> in the visuals directory."""
    stem = f"scene_{scene_index:03d}"
    for ext in sorted(MEDIA_EXTENSIONS):
        candidate = visuals_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None
