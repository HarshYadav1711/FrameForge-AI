"""Shared constants for visual assembly."""

from __future__ import annotations

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".webm", ".mkv", ".avi"})
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
