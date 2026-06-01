"""Scene segmentation pipeline — propose, group, align, constrain."""

from __future__ import annotations

import logging

from app.config import Settings
from app.core.exceptions import SegmentationError
from app.models.schemas import Scene, SceneMetadata, SegmentationResult
from app.services.segmentation.base import (
    SegmentationContext,
    build_segmentation_result,
)
from app.services.segmentation.duration import apply_duration_constraints
from app.services.segmentation.heuristic import propose_heuristic
from app.services.segmentation.llm import propose_with_gemini, propose_with_ollama
from app.services.segmentation.semantic import apply_semantic_grouping
from app.services.segmentation.timeline import apply_timestamps

logger = logging.getLogger(__name__)


class SceneSegmentationPipeline:
    """
    Reusable segmentation pipeline.

    Stages: propose → semantic group → timeline align → duration constrain → index.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(self, ctx: SegmentationContext) -> SegmentationResult:
        source = "heuristic"
        try:
            drafts, source = await self._propose(ctx)
        except SegmentationError:
            raise
        except Exception as exc:
            logger.exception("Scene proposal failed")
            raise SegmentationError(
                "Failed to propose scenes",
                cause=str(exc),
            ) from exc

        if not drafts:
            raise SegmentationError("No scenes produced from narration")

        if ctx.settings.segmentation_semantic_grouping:
            drafts = apply_semantic_grouping(drafts, ctx)

        timed = apply_timestamps(drafts, ctx.segments, ctx.total_duration)
        scenes = self._drafts_to_scenes(timed, source=source)

        scenes = apply_duration_constraints(scenes, ctx.settings)

        return build_segmentation_result(
            scenes,
            source=source,
            total_duration=ctx.total_duration,
        )

    async def _propose(self, ctx: SegmentationContext) -> tuple[list, str]:
        backend = ctx.settings.segmentation_backend.lower().strip()

        if backend == "timeline":
            from app.services.segmentation.timeline import propose_from_timeline_blocks

            if ctx.timeline_blocks:
                return propose_from_timeline_blocks(ctx.timeline_blocks), "timeline"
            raise SegmentationError(
                "Timeline segmentation requires transcript timeline blocks",
                cause="no_timeline_blocks",
            )

        if backend == "heuristic":
            return await propose_heuristic(ctx), "heuristic"

        if backend == "llm":
            drafts = await self._propose_llm(ctx)
            return drafts, "llm"

        # auto: LLM when available, else timeline, else heuristic
        if backend in ("auto", ""):
            return await self._propose_auto(ctx)

        raise SegmentationError(
            f"Unsupported segmentation backend: {backend}",
            cause="invalid_backend",
        )

    async def _propose_auto(self, ctx: SegmentationContext) -> tuple[list, str]:
        if self._llm_available(ctx.settings):
            try:
                drafts = await self._propose_llm(ctx)
                if drafts:
                    return drafts, "llm"
            except Exception as exc:
                logger.warning("LLM segmentation unavailable, falling back: %s", exc)

        if ctx.script.strip():
            drafts = await propose_heuristic(ctx)
            if drafts:
                return drafts, "heuristic"

        if ctx.timeline_blocks:
            from app.services.segmentation.timeline import propose_from_timeline_blocks

            drafts = propose_from_timeline_blocks(ctx.timeline_blocks)
            if drafts:
                return drafts, "timeline"

        return await propose_heuristic(ctx), "heuristic"

    async def _propose_llm(self, ctx: SegmentationContext) -> list:
        settings = ctx.settings
        if settings.gemini_enabled:
            try:
                drafts = await propose_with_gemini(ctx)
                logger.info("LLM segmentation via Gemini (%d scenes)", len(drafts))
                return drafts
            except Exception as exc:
                logger.warning("Gemini segmentation failed: %s", exc)

        if settings.ollama_enabled:
            drafts = await propose_with_ollama(ctx)
            logger.info("LLM segmentation via Ollama (%d scenes)", len(drafts))
            return drafts

        raise SegmentationError(
            "No LLM backend available for segmentation",
            cause="llm_unavailable",
        )

    @staticmethod
    def _llm_available(settings: Settings) -> bool:
        return settings.gemini_enabled or settings.ollama_enabled

    @staticmethod
    def _drafts_to_scenes(
        timed: list[tuple],
        *,
        source: str,
    ) -> list[Scene]:
        scenes: list[Scene] = []
        for draft, start, end in timed:
            scenes.append(
                Scene(
                    index=0,
                    title=draft.title,
                    narration=draft.narration,
                    visual_prompt=draft.visual_prompt,
                    start_time=start,
                    end_time=end,
                    metadata=SceneMetadata(
                        source=source,
                        semantic_group=draft.semantic_group,
                        transcript_segment_start=draft.transcript_segment_start,
                        transcript_segment_end=draft.transcript_segment_end,
                    ),
                )
            )
        return scenes
