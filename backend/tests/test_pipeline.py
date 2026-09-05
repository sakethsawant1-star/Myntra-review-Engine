"""
Tests for Phase 5 - End-to-End Pipeline

All external calls (DB, AI) are mocked.
"""

import json
import uuid
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone

from backend.app.connectors.base import RawEvidenceItem
from backend.app.pipeline.pipeline import Pipeline, RunStats


def _make_item(idx=1, text="I added this dress to my wishlist but the size chart is confusing."):
    return RawEvidenceItem(
        source_type="google_play",
        source_item_id=f"gp-test-{idx}",
        raw_text=text,
        content_hash=RawEvidenceItem.make_hash(text),
        rating=3.0,
    )


def _make_ai_annotation_dict():
    return {
        "wishlist_relevance": "high",
        "reason_for_saving": ["genuine_purchase_consideration"],
        "wishlist_intent": "high_purchase_intent",
        "purchase_stage": "evaluating_alternatives",
        "behaviour_after_saving": ["checked_reviews"],
        "revisit_behaviour": "unclear",
        "comparison_behaviour": "no_comparison",
        "off_platform_research": [],
        "information_sought": [],
        "workaround": ["none"],
        "purchase_trigger": ["none"],
        "abandonment_signal": ["fit_fear"],
        "frictions": [
            {
                "type": "fit_uncertainty",
                "label": "size chart",
                "severity": 2,
                "support_span": "size chart is confusing"
            }
        ],
        "emerging_themes": [],
        "intent_strength": 2,
        "conversion_relevance": 3,
        "proximity_to_purchase": "near",
        "segment_signals": ["fit_anxious"],
        "evidence_confidence": 3,
        "supporting_spans": [],
        "contradictory_signal": None,
        "analysis_notes": None,
    }


@patch("backend.app.pipeline.pipeline.AIProvider")
@patch("backend.app.pipeline.pipeline.psycopg2.connect")
def test_pipeline_happy_path(mock_connect, mock_ai_cls):
    """Happy path: 1 connector, 1 relevant item -> 1 AI annotation saved."""
    
    # Setup mock DB
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    # No existing raw evidence
    mock_cursor.fetchone.return_value = None

    # Setup mock AI
    from backend.app.ai.schema import AIAnnotation
    mock_ai = MagicMock()
    mock_ai_cls.return_value = mock_ai
    mock_ai.analyze_and_validate.return_value = (AIAnnotation(**_make_ai_annotation_dict()), {"checked": 1, "valid": 1})

    # Mock connector
    mock_connector = MagicMock()
    mock_connector.source_name = "google_play"
    mock_connector._safe_collect.return_value = [_make_item(1)]

    pipeline = Pipeline(db_url="postgresql://fake")
    stats = pipeline.run(connectors=[mock_connector])

    assert stats.raw_collected == 1
    assert stats.candidates_for_ai == 1
    assert stats.ai_success == 1
    assert stats.ai_failure == 0
    assert len(stats.warnings) == 0


@patch("backend.app.pipeline.pipeline.AIProvider")
@patch("backend.app.pipeline.pipeline.psycopg2.connect")
def test_pipeline_skips_duplicates(mock_connect, mock_ai_cls):
    """Items that already exist in the DB should be skipped."""

    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    # Simulate existing item
    mock_cursor.fetchone.return_value = ("existing-id",)

    mock_connector = MagicMock()
    mock_connector.source_name = "google_play"
    mock_connector._safe_collect.return_value = [_make_item(1)]

    pipeline = Pipeline(db_url="postgresql://fake")
    stats = pipeline.run(connectors=[mock_connector])

    assert stats.raw_collected == 1
    # Nothing new was saved -> no AI calls
    mock_ai_cls.return_value.analyze_and_validate.assert_not_called()


@patch("backend.app.pipeline.pipeline.AIProvider")
@patch("backend.app.pipeline.pipeline.psycopg2.connect")
def test_pipeline_ai_failure_is_logged(mock_connect, mock_ai_cls):
    """If AI fails after retries, it should be logged in warnings and not crash the pipeline."""
    
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = None

    mock_ai = MagicMock()
    mock_ai_cls.return_value = mock_ai
    mock_ai.analyze_and_validate.side_effect = Exception("Gemini API quota exceeded")

    mock_connector = MagicMock()
    mock_connector.source_name = "google_play"
    mock_connector._safe_collect.return_value = [_make_item(1)]

    pipeline = Pipeline(db_url="postgresql://fake")
    stats = pipeline.run(connectors=[mock_connector])

    assert stats.ai_success == 0
    assert stats.ai_failure == 1
    assert any("AI failed" in w for w in stats.warnings)


@patch("backend.app.pipeline.pipeline.AIProvider")
@patch("backend.app.pipeline.pipeline.psycopg2.connect")
def test_pipeline_noise_dropped(mock_connect, mock_ai_cls):
    """Noisy items should not reach the AI stage."""

    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = None

    mock_connector = MagicMock()
    mock_connector.source_name = "google_play"
    # This text is pure noise — use my code is a promo keyword
    noise_item = _make_item(1, text="Use my code for 50% off your next order!!")
    mock_connector._safe_collect.return_value = [noise_item]

    pipeline = Pipeline(db_url="postgresql://fake")
    stats = pipeline.run(connectors=[mock_connector])

    assert stats.noise == 1
    assert stats.candidates_for_ai == 0
    mock_ai_cls.return_value.analyze_and_validate.assert_not_called()
