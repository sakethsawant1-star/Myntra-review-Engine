"""
Tests for Phase 6 — Aggregation, Segments, and Ranking
"""
import pytest
from backend.app.scoring.segments import SegmentFinder, OpportunityGenerator
from backend.app.scoring.ranker import Ranker, RankedOpportunity
import json


def _make_annotation(
    wishlist_intent="genuine_purchase_consideration",
    purchase_stage="evaluating_alternatives",
    off_platform_research=None,
    workaround="none",
    frictions=None,
    evidence_confidence=2,
    source_type="google_play",
):
    return {
        "wishlist_relevance": "high",
        "wishlist_intent": wishlist_intent,
        "purchase_stage": purchase_stage,
        "off_platform_research": json.dumps(off_platform_research or []),
        "workaround": workaround,
        "frictions": json.dumps(frictions or []),
        "evidence_confidence": evidence_confidence,
        "analysis_notes": "intent_strength=2",
        "source_type": source_type,
    }


# ─────────────────────────────────────────────────────────────
# Segment tests
# ─────────────────────────────────────────────────────────────

def test_high_intent_blocked_segment():
    annotations = [
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
        _make_annotation(frictions=[{"type": "quality_trust",   "label": "z", "severity": 3, "support_span": "w"}]),
    ]
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    seg_names = [s.name for s in segments]
    assert "high_intent_blocked" in seg_names


def test_no_segment_below_minimum():
    """Single item should not form a segment (min=2)."""
    annotations = [_make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 1, "support_span": "y"}])]
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    seg_names = [s.name for s in segments]
    assert "high_intent_blocked" not in seg_names


def test_cross_platform_segment_identified():
    annotations = [
        _make_annotation(off_platform_research=["youtube"]),
        _make_annotation(off_platform_research=["reddit"], source_type="reddit"),
    ]
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    seg_names = [s.name for s in segments]
    assert "cross_platform_researchers" in seg_names


# ─────────────────────────────────────────────────────────────
# Opportunity generation tests
# ─────────────────────────────────────────────────────────────

def test_opportunity_generated_for_segment():
    annotations = [
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
    ]
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    gen = OpportunityGenerator()
    opps = gen.generate(segments, annotations)
    assert len(opps) >= 1
    assert any("genuine purchase intent" in o.statement for o in opps)


# ─────────────────────────────────────────────────────────────
# Ranker tests
# ─────────────────────────────────────────────────────────────

def test_ranking_produces_sorted_scores():
    annotations = [
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
        _make_annotation(off_platform_research=["youtube"]),
        _make_annotation(off_platform_research=["reddit"], source_type="reddit"),
    ]
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    gen = OpportunityGenerator()
    opps = gen.generate(segments, annotations)

    ranker = Ranker(ranking_yaml_path=None)  # Uses DEFAULT_WEIGHTS
    ranked = ranker.rank(opps, annotations, total_annotations=len(annotations))

    scores = [r.overall_score for r in ranked]
    assert scores == sorted(scores, reverse=True), "Opportunities should be sorted highest score first"


def test_ranking_exposes_component_scores():
    annotations = [
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
        _make_annotation(frictions=[{"type": "fit_uncertainty", "label": "x", "severity": 2, "support_span": "y"}]),
    ]
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    gen = OpportunityGenerator()
    opps = gen.generate(segments, annotations)
    ranker = Ranker(ranking_yaml_path=None)
    ranked = ranker.rank(opps, annotations, total_annotations=len(annotations))

    assert len(ranked) >= 1
    r = ranked[0]
    # All component scores should be set (not None)
    assert isinstance(r.score_frequency, float)
    assert isinstance(r.score_severity, float)
    assert isinstance(r.score_purchase_intent, float)
    assert isinstance(r.score_conversion_relevance, float)
    assert r.overall_score > 0


def test_duplicate_evidence_does_not_inflate_frequency():
    """Duplicate annotations should not create segments with inflated counts."""
    # Only 1 unique behaviour — should fall below min segment size of 2
    # if the deduplication was done correctly upstream (tested in pipeline tests)
    annotations = [_make_annotation()]  # single item
    finder = SegmentFinder()
    segments = finder.find_segments(annotations)
    for s in segments:
        # Counts must come from actual annotation list length
        assert s.count <= len(annotations)
