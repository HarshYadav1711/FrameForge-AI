"""Reusable subtitle styling configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.config import Settings


class SubtitleThemeDefinition(BaseModel):
    """Theme preset — colors and typography ratios (resolution-independent)."""

    name: str
    text_color: str = "#F5F5F5"
    stroke_color: str = "#0A0A0A"
    stroke_width_ratio: float = 0.0025
    background_color: str | None = None
    background_opacity: float = 0.0
    background_padding_ratio: float = 0.012
    font_weight: str = "regular"


class SubtitleStyleConfig(BaseModel):
    """User-facing style knobs (env / settings)."""

    theme: str = "cinematic"
    position: str = "bottom"
    margin_ratio: float = 0.075
    max_width_ratio: float = 0.85
    font_size_ratio: float = 0.042
    line_spacing_ratio: float = 0.35
    animation: str = "fade"
    animation_seconds: float = 0.22
    font_path: str | None = None
    enabled: bool = True


class ResolvedSubtitleStyle(BaseModel):
    """Pixel-resolved style for a specific output resolution."""

    theme_name: str
    video_width: int
    video_height: int
    font_size: int
    stroke_width: int
    line_spacing: int
    margin_x: int
    margin_y: int
    max_text_width: int
    text_color: str
    stroke_color: str
    background_color: str | None = None
    background_opacity: float = 0.0
    background_padding: int = 8
    font_path: str | None = None
    position: str = "bottom"
    animation: str = "fade"
    animation_seconds: float = 0.22

    @property
    def video_size(self) -> tuple[int, int]:
        return (self.video_width, self.video_height)


def style_config_from_settings(settings: Settings) -> SubtitleStyleConfig:
    return SubtitleStyleConfig(
        theme=settings.subtitle_theme,
        position=settings.subtitle_position,
        margin_ratio=settings.subtitle_margin_ratio,
        max_width_ratio=settings.subtitle_max_width_ratio,
        font_size_ratio=settings.subtitle_font_size_ratio,
        line_spacing_ratio=settings.subtitle_line_spacing_ratio,
        animation=settings.subtitle_animation,
        animation_seconds=settings.subtitle_animation_seconds,
        font_path=settings.subtitle_font_path or None,
        enabled=settings.subtitle_enabled,
    )


def resolve_subtitle_style(
    config: SubtitleStyleConfig,
    theme: SubtitleThemeDefinition,
    *,
    video_width: int,
    video_height: int,
) -> ResolvedSubtitleStyle:
    """Map ratio-based theme + config to concrete pixel values."""
    font_size = max(14, int(video_height * config.font_size_ratio))
    stroke_width = max(
        1,
        int(video_height * theme.stroke_width_ratio),
    )
    line_spacing = max(4, int(font_size * config.line_spacing_ratio))
    margin_x = int(video_width * config.margin_ratio)
    margin_y = int(video_height * config.margin_ratio)
    max_text_width = int(video_width * config.max_width_ratio)
    bg_pad = int(video_height * theme.background_padding_ratio)

    return ResolvedSubtitleStyle(
        theme_name=theme.name,
        video_width=video_width,
        video_height=video_height,
        font_size=font_size,
        stroke_width=stroke_width,
        line_spacing=line_spacing,
        margin_x=margin_x,
        margin_y=margin_y,
        max_text_width=max_text_width,
        text_color=theme.text_color,
        stroke_color=theme.stroke_color,
        background_color=theme.background_color,
        background_opacity=theme.background_opacity,
        background_padding=bg_pad,
        font_path=config.font_path,
        position=config.position,
        animation=config.animation,
        animation_seconds=config.animation_seconds,
    )
