"""Tests for Whisper GPU -> CPU fallback detection."""

from __future__ import annotations

from app.services.transcription.faster_whisper import (
    _cpu_fallback_settings,
    _is_gpu_runtime_error,
)
from app.config import Settings


def test_detects_cublas_missing() -> None:
    exc = RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
    assert _is_gpu_runtime_error(exc)


def test_cpu_fallback_settings() -> None:
    settings = Settings(whisper_device="cuda", whisper_compute_type="float16")
    cpu = _cpu_fallback_settings(settings)
    assert cpu.whisper_device == "cpu"
    assert cpu.whisper_compute_type == "int8"
