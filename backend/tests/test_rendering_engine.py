"""Tests for the video rendering engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.config import Settings
from app.models.schemas import RenderPhase, RenderingProgress
from app.services.rendering.cleanup import (
    partial_output_path,
    remove_partial_output,
)
from app.services.rendering.config import render_config_from_settings
from app.services.rendering.lifecycle import pipeline_percent_from_render
from app.services.rendering.metadata import build_output_metadata
from app.services.rendering.recovery import run_with_recovery


class TestRenderConfig(unittest.TestCase):
    def test_ffmpeg_params_include_faststart(self) -> None:
        config = render_config_from_settings(Settings(render_faststart=True))
        params = config.ffmpeg_params()
        self.assertIn("-movflags", params)
        self.assertIn("+faststart", params)

    def test_write_kwargs(self) -> None:
        config = render_config_from_settings(Settings())
        kwargs = config.write_kwargs()
        self.assertEqual(kwargs["codec"], "libx264")
        self.assertEqual(kwargs["audio_codec"], "aac")


class TestRenderProgress(unittest.TestCase):
    def test_pipeline_percent_mapping(self) -> None:
        progress = RenderingProgress(phase=RenderPhase.ENCODING, percent=50, message="")
        pipeline_pct = pipeline_percent_from_render(progress)
        self.assertGreaterEqual(pipeline_pct, 85)
        self.assertLessEqual(pipeline_pct, 99)


class TestCleanup(unittest.TestCase):
    def test_partial_path_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output.mp4"
            partial = partial_output_path(out)
            self.assertEqual(partial.name, "output.mp4.partial")
            partial.write_bytes(b"partial")
            remove_partial_output(out)
            self.assertFalse(partial.exists())


class TestRecovery(unittest.TestCase):
    def test_retries_then_succeeds(self) -> None:
        config = render_config_from_settings(Settings(render_max_attempts=3))
        calls = {"n": 0}

        def fn(attempt: int) -> str:
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("transient")
            return "ok"

        result = run_with_recovery(fn, config)
        self.assertEqual(result, "ok")
        self.assertEqual(calls["n"], 2)


class TestOutputMetadata(unittest.TestCase):
    def test_fallback_metadata_without_ffprobe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.mp4"
            path.write_bytes(b"\x00" * 100)
            config = render_config_from_settings(Settings())
            meta = build_output_metadata(path, config, probe=None)
            self.assertEqual(meta.file_size_bytes, 100)
            self.assertEqual(meta.width, config.width)


if __name__ == "__main__":
    unittest.main()
