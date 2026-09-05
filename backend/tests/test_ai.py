import pytest
from unittest.mock import patch, MagicMock
import json

from backend.app.ai.schema import AIAnnotation, FrictionSpan, SupportSpan
from backend.app.ai.provider import AIProvider, validate_support_spans


def test_ai_schema_valid_json():
    """A perfectly valid JSON response matching the expanded schema."""
    valid_json = {
        "wishlist_relevance": "high",
        "reason_for_saving": ["genuine_purchase_consideration"],
        "wishlist_intent": "high_purchase_intent",
        "purchase_stage": "evaluating_alternatives",
        "behaviour_after_saving": ["checked_reviews", "compared_across_platforms"],
        "revisit_behaviour": "unclear",
        "comparison_behaviour": "compared_cross_platform",
        "off_platform_research": ["youtube"],
        "information_sought": ["size accuracy"],
        "workaround": ["bought_elsewhere"],
        "purchase_trigger": ["none"],
        "abandonment_signal": ["fit_fear"],
        "frictions": [
            {
                "type": "fit_uncertainty",
                "label": "size chart confusing",
                "severity": 2,
                "support_span": "I don't understand the size chart"
            }
        ],
        "emerging_themes": ["size chart UX"],
        "intent_strength": 2,
        "conversion_relevance": 3,
        "proximity_to_purchase": "abandoned",
        "segment_signals": ["fit_anxious"],
        "evidence_confidence": 3,
        "supporting_spans": [
            {
                "claim": "User was afraid of fit",
                "exact_quote": "I don't understand the size chart"
            }
        ],
        "contradictory_signal": None,
        "analysis_notes": None,
    }

    annotation = AIAnnotation(**valid_json)
    assert annotation.wishlist_relevance == "high"
    assert len(annotation.frictions) == 1
    assert annotation.frictions[0].type == "fit_uncertainty"
    assert len(annotation.reason_for_saving) == 1
    assert len(annotation.behaviour_after_saving) == 2


def test_ai_schema_multi_valued_fields():
    """Test that list fields work with multiple values."""
    data = {
        "wishlist_relevance": "medium",
        "reason_for_saving": ["compare_alternatives", "price_monitoring"],
        "wishlist_intent": "active_comparison",
        "purchase_stage": "shortlisted",
        "behaviour_after_saving": ["compared_within_myntra", "searched_youtube", "waited"],
        "revisit_behaviour": "frequent_checking",
        "comparison_behaviour": "compared_cross_platform",
        "off_platform_research": ["youtube", "reddit", "instagram"],
        "information_sought": ["fit review", "color accuracy"],
        "workaround": ["searched_video_social", "asked_another_person"],
        "purchase_trigger": [],
        "abandonment_signal": [],
        "frictions": [
            {"type": "fit_uncertainty", "label": "sizing off", "severity": 3, "support_span": "size runs small"},
            {"type": "review_trust_uncertainty", "label": "fake reviews", "severity": 2, "support_span": "reviews seem fake"},
        ],
        "emerging_themes": [],
        "intent_strength": 2,
        "conversion_relevance": 2,
        "proximity_to_purchase": "near",
        "segment_signals": ["cross_platform_researcher"],
        "evidence_confidence": 2,
        "supporting_spans": [],
    }
    annotation = AIAnnotation(**data)
    assert len(annotation.reason_for_saving) == 2
    assert len(annotation.off_platform_research) == 3
    assert len(annotation.frictions) == 2


def test_ai_schema_expanded_friction_types():
    """Test that all new friction types are valid."""
    new_types = [
        "styling_coordination_uncertainty", "product_quality_uncertainty",
        "review_trust_uncertainty", "occasion_suitability", "social_validation",
        "comparison_difficulty", "availability_stock_concern", "delivery_timing_concern",
        "return_exchange_concern", "choice_overload", "forgetting_low_salience",
    ]
    for ftype in new_types:
        friction = FrictionSpan(type=ftype, label="test", severity=1, support_span="test quote")
        assert friction.type == ftype


@patch("backend.app.ai.provider.genai")
def test_provider_parses_response(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "wishlist_relevance": "low",
        "reason_for_saving": [],
        "wishlist_intent": "not_applicable",
        "purchase_stage": "unclear",
        "behaviour_after_saving": [],
        "revisit_behaviour": "not_applicable",
        "comparison_behaviour": "not_applicable",
        "off_platform_research": [],
        "information_sought": [],
        "workaround": [],
        "purchase_trigger": [],
        "abandonment_signal": [],
        "frictions": [],
        "emerging_themes": [],
        "intent_strength": 0,
        "conversion_relevance": 0,
        "proximity_to_purchase": "unclear",
        "segment_signals": [],
        "evidence_confidence": 1,
        "supporting_spans": [],
        "contradictory_signal": None,
        "analysis_notes": None,
    })
    mock_model.generate_content.return_value = mock_response

    provider = AIProvider()
    annotation = provider.analyze_evidence("The app crashed.")

    assert annotation.wishlist_relevance == "low"
    assert annotation.intent_strength == 0


def test_span_validation():
    """Test that support span validation works correctly."""
    source = "I loved the design but the size was completely off and I had to return it"

    annotation = AIAnnotation(
        wishlist_relevance="high",
        reason_for_saving=["genuine_purchase_consideration"],
        wishlist_intent="high_purchase_intent",
        purchase_stage="purchased",
        behaviour_after_saving=[],
        revisit_behaviour="unclear",
        comparison_behaviour="no_comparison",
        off_platform_research=[],
        information_sought=[],
        workaround=[],
        purchase_trigger=[],
        abandonment_signal=[],
        frictions=[
            FrictionSpan(
                type="fit_uncertainty",
                label="size off",
                severity=3,
                support_span="the size was completely off"
            )
        ],
        emerging_themes=[],
        intent_strength=3,
        conversion_relevance=3,
        proximity_to_purchase="completed",
        segment_signals=[],
        evidence_confidence=3,
        supporting_spans=[
            SupportSpan(claim="size problem", exact_quote="the size was completely off"),
            SupportSpan(claim="bad quote", exact_quote="this text does not exist"),
        ],
    )

    result = validate_support_spans(annotation, source)
    assert result["checked"] == 3
    assert result["valid"] == 2  # friction span + first supporting span match
    assert result["invalid"] == 1  # second supporting span doesn't match
