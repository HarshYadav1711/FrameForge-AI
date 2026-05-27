"""Semantic grouping of narration into scene drafts."""

from __future__ import annotations

import logging
import re

from app.config import Settings
from app.services.segmentation.base import SceneDraft, SegmentationContext

logger = logging.getLogger(__name__)


def apply_semantic_grouping(
    drafts: list[SceneDraft],
    ctx: SegmentationContext,
) -> list[SceneDraft]:
    """
    Group drafts by script structure when semantic grouping is enabled.

    Merges very small drafts and splits oversized groups using paragraph boundaries.
    """
    if not drafts or not ctx.settings.segmentation_semantic_grouping:
        return drafts

    if len(drafts) <= 1:
        return drafts

    # Preserve structure-aware drafts (paragraphs / timeline blocks)
    groups = {d.semantic_group for d in drafts if d.semantic_group}
    if groups and all(
        g.startswith("paragraph_") or g.startswith("block_") for g in groups
    ):
        return drafts

    target_words = _target_words_per_scene(ctx, len(drafts))
    grouped = _group_drafts_by_target(drafts, target_words)
    logger.debug(
        "Semantic grouping: %d drafts -> %d groups (target ~%d words)",
        len(drafts),
        len(grouped),
        target_words,
    )
    return grouped


def propose_from_script_structure(script: str) -> list[SceneDraft]:
    """Split script into semantic groups using paragraph and sentence boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script.strip()) if p.strip()]
    if not paragraphs:
        paragraphs = [script.strip()] if script.strip() else []

    if len(paragraphs) == 1:
        paragraphs = _split_into_sentence_groups(paragraphs[0])

    drafts: list[SceneDraft] = []
    for i, para in enumerate(paragraphs):
        title = para[:48].rstrip() + ("…" if len(para) > 48 else "")
        drafts.append(
            SceneDraft(
                title=title,
                narration=para,
                visual_prompt=f"Cinematic abstract background inspired by: {title}",
                semantic_group=f"paragraph_{i}",
            )
        )
    return drafts


def _split_into_sentence_groups(text: str, sentences_per_group: int = 3) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return [text]

    groups: list[str] = []
    buf: list[str] = []
    for sent in sentences:
        buf.append(sent)
        if len(buf) >= sentences_per_group:
            groups.append(" ".join(buf))
            buf = []
    if buf:
        groups.append(" ".join(buf))
    return groups


def _target_words_per_scene(ctx: SegmentationContext, draft_count: int) -> int:
    duration = ctx.total_duration or 60.0
    target_seconds = ctx.settings.scene_target_duration_seconds
    estimated = max(int(duration / target_seconds), 1)
    scene_count = max(estimated, min(draft_count, 8))
    total_words = sum(len(s.text.split()) for s in ctx.segments) or len(
        ctx.script.split()
    )
    return max(total_words // scene_count, 10)


def _group_drafts_by_target(
    drafts: list[SceneDraft],
    target_words: int,
) -> list[SceneDraft]:
    grouped: list[SceneDraft] = []
    buf_narration: list[str] = []
    buf_titles: list[str] = []
    buf_group: str | None = None
    word_count = 0

    def flush() -> None:
        nonlocal buf_narration, buf_titles, buf_group, word_count
        if not buf_narration:
            return
        narration = " ".join(buf_narration).strip()
        title = buf_titles[0] if buf_titles else narration[:48]
        grouped.append(
            SceneDraft(
                title=title,
                narration=narration,
                visual_prompt=(
                    f"Cinematic visual for: {title}"
                ),
                semantic_group=buf_group or "grouped",
            )
        )
        buf_narration = []
        buf_titles = []
        buf_group = None
        word_count = 0

    for draft in drafts:
        draft_words = len(draft.narration.split())
        if word_count > 0 and word_count + draft_words > target_words * 1.5:
            flush()

        buf_narration.append(draft.narration.strip())
        buf_titles.append(draft.title)
        buf_group = buf_group or draft.semantic_group
        word_count += draft_words

        if word_count >= target_words:
            flush()

    flush()
    return grouped or drafts
