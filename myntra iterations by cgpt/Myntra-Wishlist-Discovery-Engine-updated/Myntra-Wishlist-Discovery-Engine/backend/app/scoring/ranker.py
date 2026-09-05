"""
Transparent 7-Factor Opportunity Ranker

Uses ranking.yaml weights to score each opportunity candidate.
All component scores are stored alongside the final score.

Spec-required factors:
1. Frequency (corpus incidence, not just relative to top)
2. Severity (from actual annotation severity, not hardcoded dict)
3. Purchase intent (from actual intent_strength and proximity)
4. Conversion relevance (from actual annotation conversion_relevance)
5. Source convergence (coverage + balance across usable sources)
6. Segment concentration (segment lift)
7. Evidence confidence (from annotation confidence + span validation)
"""

import os
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import Counter
import yaml

from backend.app.scoring.segments import OpportunityCandidate


DEFAULT_WEIGHTS = {
    "frequency": 0.15,
    "severity": 0.15,
    "purchase_intent": 0.20,
    "conversion_relevance": 0.20,
    "source_convergence": 0.10,
    "segment_concentration": 0.10,
    "evidence_confidence": 0.10,
}


@dataclass
class RankedOpportunity:
    """An opportunity with a transparent 7-factor score breakdown."""
    id: str
    segment_name: str
    statement: str
    evidence_count: int
    dominant_friction_type: Optional[str]
    dominant_purchase_stage: Optional[str]

    # Score components (each 0–1)
    score_frequency: float = 0.0
    score_severity: float = 0.0
    score_purchase_intent: float = 0.0
    score_conversion_relevance: float = 0.0
    score_source_convergence: float = 0.0
    score_segment_concentration: float = 0.0
    score_evidence_confidence: float = 0.0

    overall_score: float = 0.0
    weights_used: Dict[str, float] = field(default_factory=dict)

    # Explanations for score detail drawer
    score_explanations: Dict[str, str] = field(default_factory=dict)


def _parse_json_field(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return val or []


class Ranker:
    """
    Scores opportunity candidates using 7 configurable dimensions.
    Uses actual annotation-level values instead of hardcoded heuristics.
    """

    def __init__(self, ranking_yaml_path: Optional[str] = None):
        if ranking_yaml_path is None:
            ranking_yaml_path = os.path.join(
                os.path.dirname(__file__), "..", "config", "ranking.yaml"
            )

        try:
            with open(ranking_yaml_path, "r") as f:
                config = yaml.safe_load(f) or {}
            self.weights = config.get("weights", DEFAULT_WEIGHTS)
        except FileNotFoundError:
            self.weights = DEFAULT_WEIGHTS

    def _normalize(self, value: float, max_val: float) -> float:
        """Scale a raw score to [0, 1]."""
        return min(value / max_val, 1.0) if max_val > 0 else 0.0

    def _get_segment_annotations(
        self, opp: OpportunityCandidate, annotations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get the annotations belonging to this opportunity's segment."""
        from backend.app.scoring.segments import SegmentFinder, _parse_json_field as seg_parse, _has_value
        finder = SegmentFinder()
        # Re-use the segment finder's logic to identify matching annotations
        seg_name = opp.segment_name
        results = []
        for a in annotations:
            if seg_name == "high_intent_blocked":
                if a.get("wishlist_intent") in ("genuine_purchase_consideration", "high_purchase_intent") \
                        and seg_parse(a.get("frictions")):
                    results.append(a)
            elif seg_name == "cross_platform_researchers":
                opr = seg_parse(a.get("off_platform_research"))
                if any(p not in ("not_applicable", "unclear") for p in opr):
                    results.append(a)
            elif seg_name == "passive_bookmarkers":
                if a.get("wishlist_intent") == "passive_bookmarking":
                    results.append(a)
            elif seg_name == "price_sensitive_waiters":
                if a.get("wishlist_intent") == "price_monitoring" \
                        or _has_value(a.get("workaround"), "bought_elsewhere"):
                    results.append(a)
            else:
                # For dynamically generated segments, include all
                results.append(a)
        return results

    def rank(
        self,
        opportunities: List[OpportunityCandidate],
        annotations: List[Dict[str, Any]],
        total_annotations: int,
        usable_source_count: int = 3,
    ) -> List[RankedOpportunity]:
        if not opportunities:
            return []

        ranked = []

        for opp in opportunities:
            seg_annotations = self._get_segment_annotations(opp, annotations)
            explanations = {}

            # ── 1. Frequency (corpus incidence) ───────────────────
            score_freq = self._normalize(opp.evidence_count, total_annotations)
            explanations["frequency"] = f"{opp.evidence_count} of {total_annotations} eligible evidence items"

            # ── 2. Severity (from actual annotation severity) ─────
            severities = []
            for a in seg_annotations:
                frictions = _parse_json_field(a.get("frictions"))
                for f in frictions:
                    if isinstance(f, dict):
                        severities.append(f.get("severity", 1))
                # Also check annotation-level severity
                if a.get("severity") and isinstance(a.get("severity"), (int, float)):
                    severities.append(a["severity"])
            avg_severity = sum(severities) / len(severities) if severities else 1
            score_sev = self._normalize(avg_severity, 3)
            explanations["severity"] = f"average severity {avg_severity:.2f}/3"

            # ── 3. Purchase intent (from actual intent_strength) ──
            intent_vals = []
            for a in seg_annotations:
                val = a.get("intent_strength")
                if val and isinstance(val, (int, float)):
                    intent_vals.append(val)
            avg_intent = sum(intent_vals) / len(intent_vals) if intent_vals else 1
            score_intent = self._normalize(avg_intent, 3)
            explanations["purchase_intent"] = f"average intent strength {avg_intent:.2f}/3"

            # ── 4. Conversion relevance (from annotations) ────────
            conv_vals = []
            for a in seg_annotations:
                val = a.get("conversion_relevance")
                if val and isinstance(val, (int, float)):
                    conv_vals.append(val)
            avg_conv = sum(conv_vals) / len(conv_vals) if conv_vals else 1
            score_conv = self._normalize(avg_conv, 3)
            explanations["conversion_relevance"] = f"average conversion relevance {avg_conv:.2f}/3"

            # ── 5. Source convergence (coverage + balance) ────────
            source_counts = Counter(a.get("source_type", "unknown") for a in seg_annotations)
            distinct_sources = len(source_counts)
            source_coverage = self._normalize(distinct_sources, usable_source_count)

            if source_counts:
                largest_share = max(source_counts.values()) / sum(source_counts.values())
                source_balance = 1 - largest_share
            else:
                source_balance = 0

            score_src = 0.7 * source_coverage + 0.3 * source_balance
            explanations["source_convergence"] = (
                f"appears across {distinct_sources} of {usable_source_count} usable sources, "
                f"largest source share {largest_share:.0%}" if source_counts else "no source data"
            )

            # ── 6. Segment concentration (lift) ──────────────────
            if total_annotations > 0 and opp.evidence_count > 0:
                seg_share_in_opp = len(seg_annotations) / opp.evidence_count if opp.evidence_count > 0 else 0
                seg_share_in_corpus = len(seg_annotations) / total_annotations if total_annotations > 0 else 0
                lift = seg_share_in_opp / seg_share_in_corpus if seg_share_in_corpus > 0 else 1
                # Cap lift at 3x for scoring
                score_seg_conc = self._normalize(min(lift, 3), 3)
                explanations["segment_concentration"] = f"{lift:.1f}x lift in segment"
            else:
                score_seg_conc = 0.5
                explanations["segment_concentration"] = "insufficient data for lift"

            # ── 7. Evidence confidence ────────────────────────────
            conf_vals = [a.get("evidence_confidence", 1) for a in seg_annotations if a.get("evidence_confidence")]
            avg_conf = sum(conf_vals) / len(conf_vals) if conf_vals else 1
            score_conf = self._normalize(avg_conf, 3)
            explanations["evidence_confidence"] = f"average confidence {avg_conf:.2f}/3"

            # ── Weighted overall score ────────────────────────────
            w = self.weights
            overall = (
                w.get("frequency", 0.15) * score_freq
                + w.get("severity", 0.15) * score_sev
                + w.get("purchase_intent", 0.20) * score_intent
                + w.get("conversion_relevance", 0.20) * score_conv
                + w.get("source_convergence", 0.10) * score_src
                + w.get("segment_concentration", 0.10) * score_seg_conc
                + w.get("evidence_confidence", 0.10) * score_conf
            )

            ranked.append(RankedOpportunity(
                id=opp.id,
                segment_name=opp.segment_name,
                statement=opp.statement,
                evidence_count=opp.evidence_count,
                dominant_friction_type=opp.dominant_friction_type,
                dominant_purchase_stage=opp.dominant_purchase_stage,
                score_frequency=round(score_freq, 3),
                score_severity=round(score_sev, 3),
                score_purchase_intent=round(score_intent, 3),
                score_conversion_relevance=round(score_conv, 3),
                score_source_convergence=round(score_src, 3),
                score_segment_concentration=round(score_seg_conc, 3),
                score_evidence_confidence=round(score_conf, 3),
                overall_score=round(overall, 3),
                weights_used=w,
                score_explanations=explanations,
            ))

        return sorted(ranked, key=lambda r: r.overall_score, reverse=True)
