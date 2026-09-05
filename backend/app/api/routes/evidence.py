"""
Evidence API Routes
Provides paginated, filterable access to raw and processed evidence.
"""

import os
import psycopg2
import psycopg2.extras
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])

def _get_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=503, detail="Database is not configured")
    try:
        return psycopg2.connect(db_url)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc

@router.get("/")
def list_evidence(
    segment: Optional[str] = None,
    source: Optional[str] = None,
    relevance: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """List evidence, optionally filtered."""
    with _get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = """
                SELECT 
                    r.id as raw_id,
                    p.id as processed_id,
                    r.source_type,
                    r.source_url,
                    r.raw_text,
                    p.relevance_status,
                    a.wishlist_intent,
                    a.purchase_stage,
                    a.frictions,
                    a.evidence_confidence
                FROM raw_evidence r
                JOIN processed_evidence p ON p.raw_evidence_id = r.id
                LEFT JOIN evidence_annotations a ON a.processed_evidence_id = p.id
                WHERE 1=1
            """
            params = []
            
            if source:
                query += " AND r.source_type = %s"
                params.append(source)
            if relevance:
                query += " AND p.relevance_status = %s"
                params.append(relevance)
                
            query += " ORDER BY r.collected_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            # Simple count query
            count_query = "SELECT count(*) FROM raw_evidence r JOIN processed_evidence p ON p.raw_evidence_id = r.id WHERE 1=1"
            count_params = []
            if source:
                count_query += " AND r.source_type = %s"
                count_params.append(source)
            if relevance:
                count_query += " AND p.relevance_status = %s"
                count_params.append(relevance)
            cur.execute(count_query, count_params)
            total = cur.fetchone()["count"]
            
            return {
                "items": [dict(r) for r in rows],
                "total": total,
                "limit": limit,
                "offset": offset
            }

@router.get("/{raw_id}")
def get_evidence_detail(raw_id: str):
    """Get full details for a single evidence item, including all annotations."""
    with _get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    r.*,
                    p.id as processed_id,
                    p.cleaned_text,
                    p.masked_text,
                    p.relevance_status,
                    p.is_duplicate,
                    a.wishlist_relevance,
                    a.reason_for_saving,
                    a.wishlist_intent,
                    a.purchase_stage,
                    a.behaviour_after_saving,
                    a.revisit_behaviour,
                    a.comparison_behaviour,
                    a.off_platform_research,
                    a.workaround,
                    a.purchase_trigger,
                    a.abandonment_signal,
                    a.frictions,
                    a.emerging_themes,
                    a.supporting_spans,
                    a.support_span_validation,
                    a.evidence_confidence,
                    a.analysis_notes
                FROM raw_evidence r
                LEFT JOIN processed_evidence p ON p.raw_evidence_id = r.id
                LEFT JOIN evidence_annotations a ON a.processed_evidence_id = p.id
                WHERE r.id = %s
            """, (raw_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Evidence not found")
                
            return dict(row)
