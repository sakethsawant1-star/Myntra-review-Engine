"""
Phase 6.2 + 6.3 - Behavioural Segment Finder & Opportunity Generator

Rule-based: uses structured annotation fields, no AI calls.
Does not hard-code which segment is the "target" — it discovers them.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json


@dataclass
class BehaviouralSegment:
    """A rule-defined user segment derived from annotation fields."""
    name: str
    description: str
    count: int
    fraction_of_total: float
    defining_fields: Dict[str, Any]


@dataclass
class OpportunityCandidate:
    """
    A product-research opportunity candidate generated from a segment.
    Format: Users with [behaviour/intent] struggle to [action] because [friction].
    """
    id: str
    segment_name: str
    statement: str
    evidence_count: int
    dominant_friction_type: Optional[str]
    dominant_purchase_stage: Optional[str]
    raw_segment_data: Dict[str, Any]


def _parse_json_field(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return val or []


def _has_value(val, value: str) -> bool:
    """Return True for both legacy scalar values and current JSON lists."""
    values = _parse_json_field(val)
    if isinstance(values, list):
        return value in values
    return values == value


class SegmentFinder:
    """
    Identifies rule-based behavioural segments from stored annotations.
    Each segment is a combination of structured annotation fields.
    """

    MIN_SEGMENT_SIZE = 2  # Minimum evidence items to promote a segment

    def find_segments(self, annotations: List[Dict[str, Any]]) -> List[BehaviouralSegment]:
        N = len(annotations)
        if N == 0:
            return []

        segments = []

        # ── Segment 1: High intent + unresolved friction ─────────────────
        high_intent_friction = [
            a for a in annotations
            if a.get("wishlist_intent") == "genuine_purchase_consideration"
            and _parse_json_field(a.get("frictions"))
        ]
        if len(high_intent_friction) >= self.MIN_SEGMENT_SIZE:
            segments.append(BehaviouralSegment(
                name="high_intent_blocked",
                description="Users who clearly want to buy but are blocked by specific frictions",
                count=len(high_intent_friction),
                fraction_of_total=len(high_intent_friction) / N,
                defining_fields={"wishlist_intent": "genuine_purchase_consideration", "has_frictions": True},
            ))

        # ── Segment 2: Cross-platform comparison shoppers ─────────────────
        comparison = [
            a for a in annotations
            if a.get("wishlist_intent") in ("genuine_purchase_consideration", "price_monitoring")
            and any(p not in ("not_applicable", "unclear") for p in _parse_json_field(a.get("off_platform_research")))
        ]
        if len(comparison) >= self.MIN_SEGMENT_SIZE:
            segments.append(BehaviouralSegment(
                name="cross_platform_researchers",
                description="Users who leave Myntra to research the product elsewhere before deciding",
                count=len(comparison),
                fraction_of_total=len(comparison) / N,
                defining_fields={"has_off_platform_research": True},
            ))

        # ── Segment 3: Passive bookmarkers with no purchase intent ────────
        bookmarkers = [
            a for a in annotations
            if a.get("wishlist_intent") == "passive_bookmarking"
        ]
        if len(bookmarkers) >= self.MIN_SEGMENT_SIZE:
            segments.append(BehaviouralSegment(
                name="passive_bookmarkers",
                description="Users saving items for inspiration with no active purchase intent",
                count=len(bookmarkers),
                fraction_of_total=len(bookmarkers) / N,
                defining_fields={"wishlist_intent": "passive_bookmarking"},
            ))

        # ── Segment 4: Price-sensitive waiters ────────────────────────────
        price_waiters = [
            a for a in annotations
            if a.get("wishlist_intent") == "price_monitoring"
            or _has_value(a.get("workaround"), "bought_elsewhere")
        ]
        if len(price_waiters) >= self.MIN_SEGMENT_SIZE:
            segments.append(BehaviouralSegment(
                name="price_sensitive_waiters",
                description="Users who add to wishlist primarily to monitor or wait for a price drop",
                count=len(price_waiters),
                fraction_of_total=len(price_waiters) / N,
                defining_fields={"wishlist_intent": "price_monitoring", "or_workaround": "bought_elsewhere"},
            ))

        return sorted(segments, key=lambda s: s.count, reverse=True)


class OpportunityGenerator:
    """
    Turns segments into structured opportunity candidate statements.
    Minimum evidence threshold must be met before promotion.
    """

    MIN_EVIDENCE = 2

    def generate(
        self,
        segments: List[BehaviouralSegment],
        annotations: List[Dict[str, Any]],
    ) -> List[OpportunityCandidate]:

        opportunities = []

        for seg in segments:
            if seg.count < self.MIN_EVIDENCE:
                continue

            # Find the dominant friction type within this segment
            relevant_annotations = self._get_segment_annotations(seg, annotations)
            all_frictions = []
            all_stages = []

            for a in relevant_annotations:
                frictions = _parse_json_field(a.get("frictions"))
                all_frictions.extend([f.get("type") for f in frictions if isinstance(f, dict)])
                all_stages.append(a.get("purchase_stage", "unclear"))

            from collections import Counter
            dominant_friction = Counter(all_frictions).most_common(1)
            dominant_stage = Counter(all_stages).most_common(1)

            dom_friction_type = dominant_friction[0][0] if dominant_friction else None
            dom_stage = dominant_stage[0][0] if dominant_stage else None

            statement = self._build_statement(seg, dom_friction_type, dom_stage)

            opportunities.append(OpportunityCandidate(
                id=f"opp_{seg.name}",
                segment_name=seg.name,
                statement=statement,
                evidence_count=seg.count,
                dominant_friction_type=dom_friction_type,
                dominant_purchase_stage=dom_stage,
                raw_segment_data=seg.defining_fields,
            ))

        return opportunities

    def _get_segment_annotations(
        self, seg: BehaviouralSegment, annotations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Re-filter annotations matching the segment definition."""
        if seg.name == "high_intent_blocked":
            return [a for a in annotations
                    if a.get("wishlist_intent") == "genuine_purchase_consideration"
                    and _parse_json_field(a.get("frictions"))]
        elif seg.name == "cross_platform_researchers":
            return [a for a in annotations
                    if any(p not in ("not_applicable", "unclear")
                           for p in _parse_json_field(a.get("off_platform_research")))]
        elif seg.name == "passive_bookmarkers":
            return [a for a in annotations if a.get("wishlist_intent") == "passive_bookmarking"]
        elif seg.name == "price_sensitive_waiters":
            return [a for a in annotations
                    if a.get("wishlist_intent") == "price_monitoring"
                    or _has_value(a.get("workaround"), "bought_elsewhere")]
        return annotations

    def _build_statement(
        self, seg: BehaviouralSegment, friction: Optional[str], stage: Optional[str]
    ) -> str:
        friction_phrase = (
            f"due to unresolved {friction.replace('_', ' ')}"
            if friction and friction not in ("unclear", "not_applicable")
            else "due to unresolved uncertainty"
        )
        stage_phrase = (
            f"while {stage.replace('_', ' ')}"
            if stage and stage not in ("unclear", "not_applicable")
            else "during their purchase journey"
        )

        templates = {
            "high_intent_blocked": (
                f"Users with genuine purchase intent struggle to complete their wishlist-to-purchase journey "
                f"{stage_phrase}, {friction_phrase}, causing delay or abandonment."
            ),
            "cross_platform_researchers": (
                f"Users with saved Myntra items leave the platform to research elsewhere {stage_phrase}, "
                f"suggesting Myntra's wishlist experience lacks the trust signals needed to convert."
            ),
            "passive_bookmarkers": (
                "Users save items to Myntra as inspiration boards with no active purchase intent, "
                "suggesting a segment that may need different re-engagement triggers."
            ),
            "price_sensitive_waiters": (
                "Users save items primarily to track prices or wait for discounts. "
                "Some purchase on competitor platforms when Myntra's price or offer is not competitive."
            ),
        }

        return templates.get(seg.name, f"Segment '{seg.name}': {seg.description}.")
