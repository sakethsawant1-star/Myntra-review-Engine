"""
Segments & Opportunities API Routes
Provides access to discovered behavioral segments and ranked opportunities.
"""

from fastapi import APIRouter, HTTPException, Query
import logging
import os
import psycopg2
import psycopg2.extras

from backend.app.scoring.segments import SegmentFinder, OpportunityGenerator
from backend.app.scoring.ranker import Ranker
from backend.app.scoring.aggregator import Aggregator

router = APIRouter(prefix="/api/segments", tags=["Segments & Opportunities"])
logger = logging.getLogger(__name__)

def get_db_url():
    return os.environ.get("DATABASE_URL")

@router.get("/")
def get_segments(scope: str = Query("fresh_sample")):
    """Returns the discovered behavioural segments based on current evidence."""
    try:
        db_url = get_db_url()
        if not db_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not set")
            
        with psycopg2.connect(db_url) as conn:
            agg = Aggregator(db_url)
            annotations = agg._fetch_annotations(conn, scope=scope)
            
            finder = SegmentFinder()
            segments = finder.find_segments(annotations)
            
            # Find overlap (rough heuristic for MVP)
            # If users are in multiple segments, we can compute overlap
            
            return {
                "total_annotations": len(annotations),
                "segments": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "count": s.count,
                        "fraction_of_total": round(s.fraction_of_total, 3),
                        "defining_fields": s.defining_fields
                    }
                    for s in segments
                ]
            }
    except Exception as e:
        logger.exception("Segment discovery failed: %s", e)
        raise HTTPException(status_code=503, detail="Segment data is unavailable") from e

@router.get("/opportunities")
def get_ranked_opportunities(scope: str = Query("fresh_sample")):
    """Returns ranked opportunity statements generated from segments."""
    try:
        db_url = get_db_url()
        if not db_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not set")
            
        with psycopg2.connect(db_url) as conn:
            agg = Aggregator(db_url)
            annotations = agg._fetch_annotations(conn, scope=scope)
            
            finder = SegmentFinder()
            segments = finder.find_segments(annotations)
            
            generator = OpportunityGenerator()
            candidates = generator.generate(segments, annotations)
            
            ranker = Ranker()
            usable_sources = max(1, len({a.get("source_type") for a in annotations if a.get("source_type")}))
            ranked = ranker.rank(candidates, annotations, len(annotations), usable_source_count=usable_sources)
            
            return {
                "opportunities": [
                    {
                        "id": r.id,
                        "segment_name": r.segment_name,
                        "statement": r.statement,
                        "evidence_count": r.evidence_count,
                        "dominant_friction_type": r.dominant_friction_type,
                        "overall_score": r.overall_score,
                        "component_scores": {
                            "frequency": r.score_frequency,
                            "severity": r.score_severity,
                            "purchase_intent": r.score_purchase_intent,
                            "conversion_relevance": r.score_conversion_relevance,
                            "source_convergence": r.score_source_convergence,
                            "segment_concentration": r.score_segment_concentration,
                            "evidence_confidence": r.score_evidence_confidence
                        },
                        "explanations": r.score_explanations
                    }
                    for r in ranked
                ]
            }
    except Exception as e:
        logger.exception("Opportunity ranking failed: %s", e)
        raise HTTPException(status_code=503, detail="Opportunity data is unavailable") from e
