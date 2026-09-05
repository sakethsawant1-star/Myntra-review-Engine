"""
Dashboard API Routes
Provides aggregated statistics for the frontend UI.
"""

from fastapi import APIRouter, HTTPException, Query
import logging
import os
import psycopg2
import psycopg2.extras

from backend.app.scoring.aggregator import Aggregator

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)

def get_db_url():
    return os.environ.get("DATABASE_URL")

@router.get("/overview")
def get_overview(scope: str = Query("fresh_sample")):
    """Returns funnel metrics and top-level summary."""
    try:
        # In a real system, you'd filter by scope. 
        # For MVP, aggregator just queries all non-duplicate evidence.
        aggregator = Aggregator(db_url=get_db_url())
        stats = aggregator.compute(scope=scope)
        
        return {
            "total_annotations": stats.get("total_annotations", 0),
            "source_distribution": stats.get("source_distribution", {}),
            "intent_x_friction": stats.get("intent_x_friction", {}),
        }
    except Exception as e:
        logger.exception("Dashboard overview failed: %s", e)
        raise HTTPException(status_code=503, detail="Dashboard data is unavailable") from e

@router.get("/behaviours")
def get_behaviours(scope: str = Query("fresh_sample")):
    """Returns detailed behavioral distributions."""
    try:
        aggregator = Aggregator(db_url=get_db_url())
        stats = aggregator.compute(scope=scope)
        
        # Remove the overview fields to keep payload tight
        stats.pop("total_annotations", None)
        stats.pop("source_distribution", None)
        stats.pop("intent_x_friction", None)
        stats.pop("population_definition", None)
        
        return stats
    except Exception as e:
        logger.exception("Dashboard behaviours failed: %s", e)
        raise HTTPException(status_code=503, detail="Dashboard data is unavailable") from e

@router.get("/questions")
def get_questions(scope: str = Query("fresh_sample")):
    """Returns the 11 discovery questions and their data coverage."""
    # This is a static mapping for MVP, demonstrating how the structured schema 
    # maps back to the 11 original problem-statement questions.
    try:
        aggregator = Aggregator(db_url=get_db_url())
        stats = aggregator.compute(scope=scope)
        
        def has_data(field):
            return field in stats and len(stats[field]) > 0
            
        questions = [
            {
                "id": "q1",
                "question": "What is the primary intent behind adding an item to the wishlist?",
                "coverage_status": "covered" if has_data("wishlist_intent") else "pending",
                "fields_used": ["wishlist_intent", "reason_for_saving"]
            },
            {
                "id": "q2",
                "question": "What percentage of wishlist items represent genuine purchase consideration?",
                "coverage_status": "covered" if has_data("wishlist_intent") else "pending",
                "fields_used": ["wishlist_intent", "intent_strength"]
            },
            {
                "id": "q3",
                "question": "How do users behave immediately after adding an item to their wishlist?",
                "coverage_status": "covered" if has_data("behaviour_after_saving") else "pending",
                "fields_used": ["behaviour_after_saving"]
            },
            {
                "id": "q4",
                "question": "What specific uncertainties prevent immediate checkout?",
                "coverage_status": "covered" if has_data("friction_distribution") else "pending",
                "fields_used": ["frictions"]
            },
            {
                "id": "q5",
                "question": "Where do users go to resolve these uncertainties?",
                "coverage_status": "covered" if has_data("off_platform_research") else "pending",
                "fields_used": ["off_platform_research", "information_sought"]
            },
            {
                "id": "q6",
                "question": "How often do users compare wishlist items across different platforms?",
                "coverage_status": "covered" if has_data("comparison_behaviour") else "pending",
                "fields_used": ["comparison_behaviour"]
            },
            {
                "id": "q7",
                "question": "What triggers a user to finally purchase a wishlisted item?",
                "coverage_status": "covered" if has_data("purchase_trigger") else "pending",
                "fields_used": ["purchase_trigger"]
            },
            {
                "id": "q8",
                "question": "What causes a user to abandon a wishlisted item?",
                "coverage_status": "covered" if has_data("abandonment_signal") else "pending",
                "fields_used": ["abandonment_signal"]
            },
            {
                "id": "q9",
                "question": "What workarounds do users employ when Myntra fails to resolve their uncertainty?",
                "coverage_status": "covered" if has_data("workaround_distribution") else "pending",
                "fields_used": ["workaround"]
            },
            {
                "id": "q10",
                "question": "Are there distinct behavioral segments within the wishlist user base?",
                "coverage_status": "covered", # Always covered by Segments API
                "fields_used": ["segment_signals", "frictions", "off_platform_research"]
            },
            {
                "id": "q11",
                "question": "Which interventions would have the highest impact on conversion?",
                "coverage_status": "covered", # Always covered by Opportunity Ranker
                "fields_used": ["conversion_relevance", "intent_strength", "frictions"]
            }
        ]
        count_fields = {
            "q1": "wishlist_intent", "q2": "wishlist_intent",
            "q3": "behaviour_after_saving", "q4": "friction_distribution",
            "q5": "off_platform_research", "q6": "comparison_behaviour",
            "q7": "purchase_trigger", "q8": "abandonment_signal",
            "q9": "workaround_distribution", "q10": "segment_signals",
            "q11": "conversion_relevance",
        }
        for question in questions:
            values = stats.get(count_fields[question["id"]], {})
            question["evidence_count"] = sum(
                value.get("count", 0) for value in values.values()
                if isinstance(value, dict)
            ) if isinstance(values, dict) else 0
        return questions
    except Exception as e:
        logger.exception("Dashboard questions failed: %s", e)
        raise HTTPException(status_code=503, detail="Dashboard data is unavailable") from e
