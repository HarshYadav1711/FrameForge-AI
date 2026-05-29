"""Tests for visual assembly pipeline."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app.config import Settings
from app.core.exceptions import VisualAssemblyError
from app.models.schemas import MediaType, Scene, SceneMetadata, TransitionType
from app.services.visual_assembly.assets import (
    find_scene_media,
    media_type_for_path,
    validate_media_asset,
)
from app.services.visual_assembly.timeline import build_visual_timeline


def _scene(index: int, start: float, end: float, image: str | None = None) -> Scene:
    return Scene(
        index=index,
        title=f"Scene {index}",
        narration="Narration text.",
        visual_prompt="A cinematic frame.",
        start_time=start,
        end_time=end,
        image_path=image,
        metadata=SceneMetadata(
            source="test",
            visual=None,
            word_count=2,
        ),
    )


class TestMediaValidation(unittest.TestCase):
    def test_media_type_for_path(self) -> None:
        self.assertEqual(media_type_for_path(Path("a.jpg")), MediaType.IMAGE)
        self.assertEqual(media_type_for_path(Path("b.MP4")), MediaType.VIDEO)
        self.assertIsNone(media_type_for_path(Path("c.gif")))

    def test_validate_image(self) -> None:
        settings = Settings()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.png"
            Image.new("RGB", (640, 360), (10, 20, 30)).save(path)
            asset = validate_media_asset(path, settings)
            self.assertEqual(asset.media_type, MediaType.IMAGE)
            self.assertEqual(asset.width, 640)

    def test_validate_missing_file(self) -> None:
        with self.assertRaises(VisualAssemblyError):
            validate_media_asset(Path("/nonexistent/file.jpg"), Settings())

    def test_find_scene_media(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scene_002.webp").write_bytes(b"not-a-real-image")
            found = find_scene_media(root, 2)
            self.assertEqual(found, root / "scene_002.webp")
            self.assertIsNone(find_scene_media(root, 1))


class TestVisualTimeline(unittest.TestCase):
    def test_build_timeline_from_scenes(self) -> None:
        settings = Settings(visual_default_transition="fade")
        scenes = [
            _scene(1, 0.0, 5.0, "/tmp/s1.jpg"),
            _scene(2, 5.0, 10.0, "/tmp/s2.jpg"),
        ]
        timeline = build_visual_timeline(scenes, 10.0, settings)
        self.assertEqual(len(timeline.entries), 2)
        self.assertEqual(timeline.entries[0].duration, 5.0)
        self.assertEqual(timeline.entries[0].transition_in, TransitionType.FADE)
        self.assertEqual(timeline.metadata.entry_count, 2)

    def test_timeline_extends_to_total_duration(self) -> None:
        scenes = [_scene(1, 0.0, 8.0, "/tmp/s1.jpg")]
        timeline = build_visual_timeline(scenes, 10.0, Settings())
        self.assertEqual(timeline.entries[-1].end, 10.0)


if __name__ == "__main__":
    unittest.main()
