"""
Deterministic Aggregator — Refined for Phase 9

Reads all stored evidence_annotations from Supabase and computes
distribution statistics using structured columns. Every percentage 
exposes its denominator.
"""

import os
from collections import defaultdict, Counter
from typing import Any, Dict, List, Optional
import psycopg2
import psycopg2.extras
import json


def _pct(numerator: int, denominator: int) -> Dict[str, Any]:
    """Return a transparent fraction dict. Never divides by zero."""
    return {
        "count": numerator,
        "denominator": denominator,
        "percent": round(100 * numerator / denominator, 1) if denominator > 0 else 0.0,
    }

def _parse_json_field(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return val or []


class Aggregator:
    """
    Reads from the DB and produces distribution stats from stored annotations.
    All outputs include their denominator so percentages are fully auditable.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL is not set.")

    def _get_conn(self):
        return psycopg2.connect(self.db_url)

    def _fetch_annotations(self, conn, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = """
                SELECT
                    ea.id AS annotation_id,
                    ea.wishlist_relevance,
                    ea.wishlist_intent,
                    ea.purchase_stage,
                    ea.intent_strength,
                    ea.severity,
                    ea.conversion_relevance,
                    ea.proximity_to_purchase_label,
                    ea.reason_for_saving,
                    ea.behaviour_after_saving,
                    ea.revisit_behaviour,
                    ea.comparison_behaviour,
                    ea.off_platform_research,
                    ea.information_sought,
                    ea.workaround,
                    ea.purchase_trigger,
                    ea.abandonment_signal,
                    ea.frictions,
                    ea.emerging_themes,
                    ea.segment_signals,
                    ea.evidence_confidence,
                    re.source_type,
                    cr.dataset_scope
                FROM evidence_annotations ea
                JOIN processed_evidence pe ON pe.id = ea.processed_evidence_id
                JOIN raw_evidence re ON re.id = pe.raw_evidence_id
                LEFT JOIN collection_runs cr ON cr.id = re.collection_run_id
                WHERE pe.is_duplicate = FALSE
                  AND pe.relevance_status != 'noise'
            """
            params = []
            if scope:
                query += " AND cr.dataset_scope = %s"
                params.append(scope)
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def _dist(self, annotations: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
        """Compute distribution for a scalar field."""
        N = len(annotations)
        counts = Counter(a.get(field) for a in annotations if a.get(field))
        return {val: _pct(count, N) for val, count in counts.most_common()}

    def _dist_list(self, annotations: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
        """Compute distribution for a list field (JSON array)."""
        N = len(annotations)
        all_vals = []
        for a in annotations:
            vals = _parse_json_field(a.get(field))
            all_vals.extend([x for x in vals if x not in ("not_applicable", "unclear")])
        counts = Counter(all_vals)
        return {val: _pct(count, N) for val, count in counts.most_common()}

    def compute(self, scope: Optional[str] = None) -> Dict[str, Any]:
        conn = self._get_conn()
        try:
            annotations = self._fetch_annotations(conn, scope=scope)
        finally:
            conn.close()

        N = len(annotations)

        if N == 0:
            return {"total_annotations": 0, "note": "No annotations found."}

        # Source distribution
        source_distribution = self._dist(annotations, "source_type")
        
        # Intent & Stage
        wishlist_relevance = self._dist(annotations, "wishlist_relevance")
        wishlist_intent = self._dist(annotations, "wishlist_intent")
        purchase_stage = self._dist(annotations, "purchase_stage")
        conversion_relevance = self._dist(annotations, "conversion_relevance")
        revisit_behaviour = self._dist(annotations, "revisit_behaviour")
        comparison_behaviour = self._dist(annotations, "comparison_behaviour")
        proximity = self._dist(annotations, "proximity_to_purchase_label")

        # Multi-value fields
        reason_for_saving = self._dist_list(annotations, "reason_for_saving")
        behaviour_after_saving = self._dist_list(annotations, "behaviour_after_saving")
        off_platform_research = self._dist_list(annotations, "off_platform_research")
        workaround_distribution = self._dist_list(annotations, "workaround")
        purchase_trigger = self._dist_list(annotations, "purchase_trigger")
        abandonment_signal = self._dist_list(annotations, "abandonment_signal")
        segment_signals = self._dist_list(annotations, "segment_signals")

        # Frictions
        all_frictions = []
        for a in annotations:
            frictions_raw = _parse_json_field(a.get("frictions"))
            all_frictions.extend(frictions_raw)

        friction_types = Counter(f.get("type", "unknown") for f in all_frictions if isinstance(f, dict))
        total_friction_mentions = len(all_frictions)
        friction_distribution = {
            ftype: {
                "count": count,
                "of_total_friction_mentions": _pct(count, total_friction_mentions),
                "of_all_annotations": _pct(count, N),
            }
            for ftype, count in friction_types.most_common()
        }

        # Intent x Friction Funnel (using actual intent_strength)
        high_intent = [
            a for a in annotations 
            if a.get("intent_strength") and a["intent_strength"] >= 2
        ]
        high_intent_with_friction = [
            a for a in high_intent 
            if _parse_json_field(a.get("frictions"))
        ]
        intent_x_friction = {
            "high_intent_total": _pct(len(high_intent), N),
            "high_intent_with_friction": _pct(len(high_intent_with_friction), len(high_intent) if high_intent else 1),
        }

        return {
            "total_annotations": N,
            "population_definition": "Non-duplicate, non-noise evidence annotations",
            "source_distribution": source_distribution,
            "wishlist_relevance": wishlist_relevance,
            "wishlist_intent": wishlist_intent,
            "purchase_stage": purchase_stage,
            "conversion_relevance": conversion_relevance,
            "revisit_behaviour": revisit_behaviour,
            "comparison_behaviour": comparison_behaviour,
            "proximity_to_purchase": proximity,
            "reason_for_saving": reason_for_saving,
            "behaviour_after_saving": behaviour_after_saving,
            "off_platform_research": off_platform_research,
            "workaround_distribution": workaround_distribution,
            "purchase_trigger": purchase_trigger,
            "abandonment_signal": abandonment_signal,
            "segment_signals": segment_signals,
            "friction_distribution": friction_distribution,
            "intent_x_friction": intent_x_friction,
        }
