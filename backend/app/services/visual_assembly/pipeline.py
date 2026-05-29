"""Visual assembly pipeline: attach, validate, preprocess, normalize."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings
from app.core.exceptions import VisualAssemblyError
from app.models.schemas import (
    MediaType,
    Scene,
    SceneMetadata,
    SceneVisualMetadata,
    TransitionType,
    VisualTimeline,
)
from app.services.visual_assembly.assets import find_scene_media, validate_media_asset
from app.services.visual_assembly.normalize import normalize_for_render
from app.services.visual_assembly.preprocess import preprocess_media
from app.services.visual_assembly.timeline import build_visual_timeline
from app.services.visual_assembly.generator import generate_scene_visual

logger = logging.getLogger(__name__)


def _default_transition(settings: Settings) -> TransitionType:
    try:
        return TransitionType(settings.visual_default_transition.lower())
    except ValueError:
        return TransitionType.FADE


def _transition_duration(transition: TransitionType, settings: Settings) -> float:
    if transition == TransitionType.CROSSFADE:
        return settings.visual_crossfade_seconds
    return settings.visual_transition_seconds


def _write_video_poster(video_path: Path, poster_path: Path, settings: Settings) -> None:
    from PIL import Image

    from app.services.subtitles.moviepy_compat import import_video_file_clip
    from app.services.visual_assembly.normalize import normalize_image_for_render

    VideoFileClip = import_video_file_clip()
    clip = VideoFileClip(str(video_path))
    try:
        frame = clip.get_frame(0)
    finally:
        clip.close()

    tmp = poster_path.with_suffix(".tmp.png")
    Image.fromarray(frame).save(tmp, format="PNG")
    normalize_image_for_render(tmp, poster_path, settings)
    tmp.unlink(missing_ok=True)


def _attach_external_visual(
    scene: Scene,
    source: Path,
    visuals_dir: Path,
    settings: Settings,
) -> Scene:
    try:
        asset = validate_media_asset(source, settings)
    except VisualAssemblyError as exc:
        raise VisualAssemblyError(
            exc.message,
            scene_index=scene.index,
            cause=exc.cause,
        ) from exc

    work_dir = visuals_dir / "work" / f"scene_{scene.index:03d}"
    preprocessed = preprocess_media(asset, work_dir)
    norm_dir = visuals_dir / "normalized"
    normalized_path, media_type = normalize_for_render(
        asset, preprocessed, norm_dir, settings
    )

    transition = _default_transition(settings)
    render_still = normalized_path
    if media_type == MediaType.VIDEO:
        poster = norm_dir / f"scene_{scene.index:03d}_poster.jpg"
        _write_video_poster(asset.path, poster, settings)
        render_still = poster

    visual_meta = SceneVisualMetadata(
        media_type=media_type,
        source_path=str(source.resolve()),
        normalized_path=str(normalized_path.resolve()),
        transition_in=transition,
        transition_duration_seconds=_transition_duration(transition, settings),
        width=asset.width,
        height=asset.height,
        duration_seconds=asset.duration_seconds,
    )

    meta = scene.metadata or SceneMetadata(source="assembly")
    updated_meta = meta.model_copy(update={"visual": visual_meta})

    return scene.model_copy(
        update={
            "image_path": str(render_still.resolve()),
            "metadata": updated_meta,
        }
    )


def _attach_generated_visual(
    scene: Scene,
    visuals_dir: Path,
    settings: Settings,
) -> Scene:
    out = visuals_dir / f"scene_{scene.index:03d}.jpg"
    path = generate_scene_visual(scene, out, settings)
    transition = _default_transition(settings)
    visual_meta = SceneVisualMetadata(
        media_type=MediaType.GENERATED,
        source_path=None,
        normalized_path=path,
        transition_in=transition,
        transition_duration_seconds=_transition_duration(transition, settings),
        width=settings.video_width,
        height=settings.video_height,
    )
    meta = scene.metadata or SceneMetadata(source="generated")
    updated_meta = meta.model_copy(update={"visual": visual_meta})
    return scene.model_copy(update={"image_path": path, "metadata": updated_meta})


def assemble_scene_visuals(
    scenes: list[Scene],
    visuals_dir: Path,
    settings: Settings,
    *,
    total_duration: float = 0.0,
) -> tuple[list[Scene], VisualTimeline]:
    """
    Attach visuals to every scene and build the visual timeline.

    Uses scene_NNN.<ext> in visuals_dir when present; otherwise generates placeholders.
    """
    if not scenes:
        raise VisualAssemblyError("No scenes to assemble visuals for")

    visuals_dir.mkdir(parents=True, exist_ok=True)
    updated: list[Scene] = []

    for scene in scenes:
        external = find_scene_media(visuals_dir, scene.index)
        try:
            if external:
                updated.append(
                    _attach_external_visual(scene, external, visuals_dir, settings)
                )
            else:
                updated.append(_attach_generated_visual(scene, visuals_dir, settings))
        except VisualAssemblyError:
            raise
        except Exception as exc:
            raise VisualAssemblyError(
                f"Failed to attach visual for scene {scene.index}",
                scene_index=scene.index,
                cause=str(exc),
            ) from exc

    timeline = build_visual_timeline(updated, total_duration, settings)
    logger.info(
        "Assembled visuals for %d scenes (%d timeline entries)",
        len(updated),
        len(timeline.entries),
    )
    return updated, timeline
