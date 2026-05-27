"""LLM-backed scene proposers (Ollama, Gemini)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import Settings
from app.services.segmentation.base import SceneDraft, SegmentationContext

logger = logging.getLogger(__name__)

SEGMENT_PROMPT = """You are a video editor assistant. Split the following script into distinct visual scenes for a narrated video.

Rules:
- Return ONLY valid JSON (no markdown fences).
- Each scene needs: title (short), narration (exact script portion), visual_prompt (one sentence describing visuals).
- Preserve the full script across scenes — do not omit text.
- Aim for 3-8 scenes depending on length.
- Match pacing to the transcript timing when provided.

Script:
{script}

Transcript timing reference:
{transcript_summary}

Respond with JSON array:
[
  {{"title": "...", "narration": "...", "visual_prompt": "..."}}
]
"""


def transcript_summary(ctx: SegmentationContext) -> str:
    if ctx.timeline_blocks:
        lines = [
            f"[{b.start:.1f}s-{b.end:.1f}s] {b.text}"
            for b in ctx.timeline_blocks[:30]
        ]
        if len(ctx.timeline_blocks) > 30:
            lines.append(f"... and {len(ctx.timeline_blocks) - 30} more blocks")
        return "\n".join(lines)

    if not ctx.segments:
        return "No transcript available."
    lines = [f"[{s.start:.1f}s-{s.end:.1f}s] {s.text}" for s in ctx.segments[:40]]
    if len(ctx.segments) > 40:
        lines.append(f"... and {len(ctx.segments) - 40} more segments")
    return "\n".join(lines)


def parse_scenes_json(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in LLM response")
    return json.loads(text[start : end + 1])


def drafts_from_llm_items(items: list[dict[str, Any]]) -> list[SceneDraft]:
    drafts: list[SceneDraft] = []
    for i, item in enumerate(items):
        narration = str(item.get("narration", "")).strip()
        if not narration:
            continue
        drafts.append(
            SceneDraft(
                title=str(item.get("title", f"Scene {i + 1}")),
                narration=narration,
                visual_prompt=str(
                    item.get("visual_prompt", "Minimal dark cinematic gradient")
                ),
                semantic_group=f"llm_scene_{i}",
            )
        )
    return drafts


async def propose_with_ollama(ctx: SegmentationContext) -> list[SceneDraft]:
    settings = ctx.settings
    prompt = SEGMENT_PROMPT.format(
        script=ctx.script.strip(),
        transcript_summary=transcript_summary(ctx),
    )
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    items = parse_scenes_json(data.get("response", ""))
    return drafts_from_llm_items(items)


async def propose_with_gemini(ctx: SegmentationContext) -> list[SceneDraft]:
    settings = ctx.settings
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is required when Gemini is enabled")

    prompt = SEGMENT_PROMPT.format(
        script=ctx.script.strip(),
        transcript_summary=transcript_summary(ctx),
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    params = {"key": settings.gemini_api_key}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, params=params, json=body)
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    items = parse_scenes_json(text)
    return drafts_from_llm_items(items)
