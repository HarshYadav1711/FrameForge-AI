"""Configurable subtitle theme presets."""

from __future__ import annotations

from app.services.subtitles.config import SubtitleThemeDefinition

THEME_PRESETS: dict[str, SubtitleThemeDefinition] = {
    "cinematic": SubtitleThemeDefinition(
        name="cinematic",
        text_color="#F2F2F2",
        stroke_color="#121212",
        stroke_width_ratio=0.0028,
        background_color=None,
        background_opacity=0.0,
    ),
    "minimal": SubtitleThemeDefinition(
        name="minimal",
        text_color="#FFFFFF",
        stroke_color="#404040",
        stroke_width_ratio=0.0018,
        background_color=None,
        background_opacity=0.0,
    ),
    "bold": SubtitleThemeDefinition(
        name="bold",
        text_color="#FFFFFF",
        stroke_color="#000000",
        stroke_width_ratio=0.004,
        background_color="#000000",
        background_opacity=0.62,
        background_padding_ratio=0.018,
    ),
    "documentary": SubtitleThemeDefinition(
        name="documentary",
        text_color="#E8E4DC",
        stroke_color="#1C1C1C",
        stroke_width_ratio=0.0022,
        background_color="#1A1A1A",
        background_opacity=0.45,
        background_padding_ratio=0.014,
    ),
    "high_contrast": SubtitleThemeDefinition(
        name="high_contrast",
        text_color="#FFFF00",
        stroke_color="#000000",
        stroke_width_ratio=0.0035,
        background_color="#000000",
        background_opacity=0.75,
        background_padding_ratio=0.016,
    ),
}

DEFAULT_THEME = "cinematic"


def get_theme(name: str) -> SubtitleThemeDefinition:
    key = name.lower().strip()
    if key in THEME_PRESETS:
        return THEME_PRESETS[key]
    return THEME_PRESETS[DEFAULT_THEME]
