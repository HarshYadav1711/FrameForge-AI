"""Tests for pipeline profile resolution."""

from __future__ import annotations

from app.config import Settings, resolve_pipeline_settings


def test_fast_profile_disables_llm_and_lowers_resolution() -> None:
    settings = Settings(pipeline_profile="fast")
    resolved = resolve_pipeline_settings(settings)

    assert resolved.ollama_enabled is False
    assert resolved.video_width <= 1280
    assert resolved.video_height <= 720
    assert resolved.render_preset == "veryfast"
    assert resolved.subtitle_animation == "none"


def test_quality_profile_enables_llm() -> None:
    settings = Settings(pipeline_profile="quality", ollama_enabled=False)
    resolved = resolve_pipeline_settings(settings)

    assert resolved.ollama_enabled is True
    assert resolved.render_preset == "medium"
    assert resolved.whisper_beam_size == 5
