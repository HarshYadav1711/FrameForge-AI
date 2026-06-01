"""Heuristic scene proposer (no LLM required)."""

from __future__ import annotations

import logging

from app.services.segmentation.base import SceneDraft, SegmentationContext
from app.services.segmentation.semantic import propose_from_script_structure
from app.services.segmentation.timeline import propose_from_timeline_blocks

logger = logging.getLogger(__name__)


async def propose_heuristic(ctx: SegmentationContext) -> list[SceneDraft]:
    """Fallback proposer — script text first; transcript blocks only for timing hints."""
    if ctx.script.strip():
        drafts = propose_from_script_structure(ctx.script)
        if drafts:
            logger.info("Heuristic: %d scenes from script structure", len(drafts))
            return drafts

    if ctx.timeline_blocks:
        drafts = propose_from_timeline_blocks(ctx.timeline_blocks)
        if drafts:
            logger.info("Heuristic: %d scenes from timeline blocks (no script)", len(drafts))
            return drafts

    return []
