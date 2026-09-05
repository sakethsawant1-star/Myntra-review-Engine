"""Grounded dashboard assistant."""

import json
import logging
import os
from collections import Counter
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.scoring.aggregator import Aggregator, _parse_json_field
from backend.app.scoring.ranker import Ranker
from backend.app.scoring.segments import OpportunityGenerator, SegmentFinder

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    _GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str


_SYSTEM_PROMPT = """You are a research assistant for the Myntra Wishlist Discovery Engine.
Answer using ONLY the dashboard data below. Do not invent statistics, friction types,
segments, causes, or product recommendations. If the data is insufficient, say so.
Keep the answer concise (2-4 sentences), factual, and plain text.

Dashboard data:
{context}
"""


def _build_context(db_conn) -> str:
    """Build grounded context from the tables that actually exist in this project."""
    annotations = Aggregator(os.environ.get("DATABASE_URL"))._fetch_annotations(db_conn)
    total = len(annotations)
    high_intent = sum(1 for item in annotations if item.get("intent_strength", 0) >= 2)

    friction_counts = Counter()
    for item in annotations:
        for friction in _parse_json_field(item.get("frictions")):
            if isinstance(friction, dict) and friction.get("type"):
                friction_counts[friction["type"]] += 1

    segments = SegmentFinder().find_segments(annotations)
    candidates = OpportunityGenerator().generate(segments, annotations)
    ranked = Ranker().rank(
        candidates,
        annotations,
        total,
        usable_source_count=max(1, len({item.get("source_type") for item in annotations if item.get("source_type")})),
    )

    return json.dumps(
        {
            "total_annotated": total,
            "high_purchase_intent_count": high_intent,
            "top_frictions": [
                {"type": name, "count": count}
                for name, count in friction_counts.most_common(5)
            ],
            "behavioral_segments": [
                {"name": segment.name, "count": segment.count, "fraction": round(segment.fraction_of_total, 3)}
                for segment in segments[:6]
            ],
            "top_opportunities": [
                {
                    "statement": opportunity.statement,
                    "score": opportunity.overall_score,
                    "evidence": opportunity.evidence_count,
                    "friction": opportunity.dominant_friction_type,
                }
                for opportunity in ranked[:3]
            ],
        },
        indent=2,
    )


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not _GENAI_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI provider is not available")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI provider is not configured")

    try:
        import psycopg2

        with psycopg2.connect(os.environ.get("DATABASE_URL", "")) as conn:
            context = _build_context(conn)
    except Exception as exc:
        logger.warning("[Chat] Could not load dashboard context: %s", exc)
        raise HTTPException(status_code=503, detail="Dashboard data is unavailable") from exc

    history_text = "\n".join(
        f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
        for msg in (req.history or [])[-6:]
    )
    prompt = f"{_SYSTEM_PROMPT.format(context=context)}\n{history_text}\nUser: {req.question}\nAssistant:"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
        response = model.generate_content(prompt)
        return ChatResponse(answer=response.text.strip())
    except Exception as exc:
        logger.error("[Chat] Gemini call failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI inference failed") from exc
