"""Queue and inspect pipeline runs.

The API service stays lightweight: it creates a queued run and returns its id.
The free GitHub Actions worker claims and executes queued runs.
"""

import json
import os
import uuid
from typing import List

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

ALLOWED_SOURCES = {"google_play", "apple_store", "reddit_rss", "reddit", "youtube"}


class PipelineRunRequest(BaseModel):
    dataset_scope: str = "fresh_sample"
    item_cap: int = Field(default=40, ge=1, le=500)
    sources: List[str] = Field(default_factory=lambda: ["google_play", "reddit_rss"])

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, sources: List[str]) -> List[str]:
        cleaned = list(dict.fromkeys(sources))
        invalid = sorted(set(cleaned) - ALLOWED_SOURCES)
        if invalid:
            raise ValueError(f"Unsupported sources: {', '.join(invalid)}")
        if not cleaned:
            raise ValueError("At least one source is required")
        return cleaned


def _get_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=503, detail="Database is not configured")
    try:
        return psycopg2.connect(db_url)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc


@router.post("/runs", status_code=202)
def trigger_pipeline_run(req: PipelineRunRequest):
    """Queue a run for the next GitHub Actions worker execution."""
    cooldown = int(os.environ.get("SAMPLE_RUN_COOLDOWN_SECONDS", 300))
    run_id = str(uuid.uuid4())

    with _get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM collection_runs
                WHERE requested_at > NOW() - (%s * INTERVAL '1 second')
                  AND dataset_scope = %s
                  AND status IN ('queued', 'running')
                LIMIT 1
                """,
                (cooldown, req.dataset_scope),
            )
            if cur.fetchone():
                raise HTTPException(status_code=429, detail=f"Please wait {cooldown} seconds between pipeline runs.")

            cur.execute(
                """
                INSERT INTO collection_runs
                    (id, run_type, status, dataset_scope, requested_item_cap,
                     requested_sources, enabled_sources, items_collected,
                     items_retained, requested_at, heartbeat_at)
                VALUES (%s, 'api_trigger', 'queued', %s, %s, %s, %s, 0, 0, NOW(), NOW())
                """,
                (
                    run_id,
                    req.dataset_scope,
                    req.item_cap,
                    json.dumps(req.sources),
                    json.dumps(req.sources),
                ),
            )
        conn.commit()

    return {
        "status": "queued",
        "run_id": run_id,
        "message": "Run queued. The GitHub Actions worker will process it on its next execution.",
    }


@router.get("/runs/latest")
def get_latest_run(scope: str = Query("fresh_sample")):
    with _get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM collection_runs
                WHERE dataset_scope = %s
                ORDER BY COALESCE(requested_at, started_at) DESC
                LIMIT 1
                """,
                (scope,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="No runs found")
            return dict(row)


@router.get("/runs/{run_id}")
def get_run_status(run_id: str):
    with _get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM collection_runs WHERE id = %s", (run_id,))
            run = cur.fetchone()
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")

            cur.execute(
                """
                SELECT sequence_number, stage_key, stage_label, status,
                       input_count, output_count, rejected_count, duration_ms,
                       started_at, completed_at, warnings, error_message
                FROM collection_run_stages
                WHERE run_id = %s
                ORDER BY sequence_number ASC
                """,
                (run_id,),
            )
            result = dict(run)
            result["stages"] = [dict(stage) for stage in cur.fetchall()]
            return result
