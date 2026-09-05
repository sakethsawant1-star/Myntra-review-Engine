"""
End-to-End Enrichment Pipeline Orchestrator — Refined

Runs the full pipeline in sequence:
  1. Create collection run + stage records
  2. Collect raw evidence from connectors
  3. Save raw evidence to Supabase
  4. Normalize text
  5. Mask PII
  6. Deduplicate
  7. Relevance candidate filter
  8. AI behavioural enrichment + span validation
  9. Complete run with counts

Key refinement: persists ALL annotation fields, stores processed_evidence
for EVERY raw item (not just AI candidates), and writes stage records.
"""

import os
import uuid
import time
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras

from backend.app.connectors.base import SourceConnector, RawEvidenceItem
from backend.app.pipeline.preprocessor import Preprocessor
from backend.app.ai.provider import AIProvider
from backend.app.ai.schema import AIAnnotation
from backend.app.scoring.aggregator import Aggregator
from backend.app.scoring.segments import SegmentFinder, OpportunityGenerator
from backend.app.scoring.ranker import Ranker

SCHEMA_VERSION = "v2.0.0"
ANALYSIS_VERSION = "v2.0.0"
PROCESSING_VERSION = "v2.0.0"
RANKING_VERSION = "v1.0.0"

STAGE_KEYS = [
    ("collect", "Collect public conversations"),
    ("normalize", "Normalize text"),
    ("mask_pii", "Mask personal information"),
    ("deduplicate", "Remove duplicates"),
    ("relevance_filter", "Filter decision-relevant evidence"),
    ("ai_extract", "Extract behavior with AI"),
    ("validate_evidence", "Validate evidence spans"),
    ("aggregate", "Aggregate behavioral patterns"),
    ("rank_opportunities", "Rank opportunity hypotheses"),
]


@dataclass
class RunStats:
    """Tracks statistics for a single pipeline run."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_type: str = "manual"
    dataset_scope: str = "fresh_sample"
    source_config_version: str = SCHEMA_VERSION

    raw_collected: int = 0
    unique_items: int = 0
    duplicates: int = 0
    noise: int = 0
    candidate_rejected: int = 0
    unsupported_language: int = 0
    candidates_for_ai: int = 0
    ai_success: int = 0
    ai_failure: int = 0

    warnings: List[str] = field(default_factory=list)
    stage_durations: Dict[str, float] = field(default_factory=dict)
    successful_sources: List[str] = field(default_factory=list)
    failed_sources: List[str] = field(default_factory=list)

    def items_retained(self) -> int:
        return self.ai_success


class Pipeline:
    """
    Wires together all pipeline stages for a single collection run.
    Stores processed_evidence for EVERY raw item and persists ALL annotation fields.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL is not set.")

        self.preprocessor = Preprocessor()
        self.ai = AIProvider()
        self.model_name = self.ai.model_name

    def _get_conn(self):
        return psycopg2.connect(self.db_url)

    # ──────────────────────────────────────────────
    # Stage helpers: run and stage management
    # ──────────────────────────────────────────────
    def _create_run(self, conn, stats: RunStats, requested_sources=None, item_cap=None):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collection_runs
                    (id, run_type, status, source_config_version, dataset_scope,
                     requested_item_cap, requested_sources, model_provider, model_name,
                     analysis_version, processing_version,
                     items_collected, items_retained, requested_at, started_at)
                VALUES (%s, %s, 'queued', %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, NOW(), NOW())
                """,
                (
                    stats.run_id, stats.run_type, stats.source_config_version,
                    stats.dataset_scope, item_cap,
                    json.dumps(requested_sources) if requested_sources else None,
                    "gemini", self.model_name,
                    ANALYSIS_VERSION, PROCESSING_VERSION,
                ),
            )
            # Create all stage records as 'pending'
            for seq, (key, label) in enumerate(STAGE_KEYS, 1):
                cur.execute(
                    """
                    INSERT INTO collection_run_stages
                        (id, run_id, sequence_number, stage_key, stage_label, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                    ON CONFLICT (run_id, stage_key) DO NOTHING
                    """,
                    (str(uuid.uuid4()), stats.run_id, seq, key, label),
                )
        conn.commit()
        self._update_run_status(conn, stats, "running")
        print(f"[Pipeline] Created collection run: {stats.run_id}")

    def _update_run_status(self, conn, stats: RunStats, status: str, stage: str = None):
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE collection_runs
                SET status=%s, current_stage=%s, heartbeat_at=NOW()
                WHERE id=%s
                """,
                (status, stage, stats.run_id),
            )
        conn.commit()

    def _start_stage(self, conn, run_id: str, stage_key: str, input_count: int = 0):
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE collection_run_stages
                SET status='running', started_at=NOW(), input_count=%s
                WHERE run_id=%s AND stage_key=%s
                """,
                (input_count, run_id, stage_key),
            )
        conn.commit()

    def _complete_stage(self, conn, run_id: str, stage_key: str,
                        output_count: int = 0, rejected_count: int = 0,
                        warnings: List[str] = None, error: str = None):
        status = "failed" if error else ("completed_with_warnings" if warnings else "completed")
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE collection_run_stages
                SET status=%s, completed_at=NOW(),
                    duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000,
                    output_count=%s, rejected_count=%s,
                    warnings=%s, error_message=%s
                WHERE run_id=%s AND stage_key=%s
                """,
                (
                    status, output_count, rejected_count,
                    json.dumps(warnings) if warnings else None, error,
                    run_id, stage_key,
                ),
            )
        conn.commit()

    # ──────────────────────────────────────────────
    # Stage 1: Collect raw evidence
    # ──────────────────────────────────────────────
    def _collect_and_save_raw(
        self, conn, connectors: List[SourceConnector], stats: RunStats,
        item_cap: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        self._start_stage(conn, stats.run_id, "collect", 0)
        self._update_run_status(conn, stats, "running", "collect")
        t0 = time.time()
        all_items = []

        remaining = item_cap
        remaining_connectors = len(connectors)
        for connector in connectors:
            try:
                source_limit = None
                if remaining is not None:
                    source_limit = max(1, (remaining + remaining_connectors - 1) // remaining_connectors)
                items = connector._safe_collect(limit=source_limit)
                print(f"[Pipeline] {connector.source_name}: {len(items)} raw items.")
                all_items.extend(items)
                stats.successful_sources.append(connector.source_name)
                if remaining is not None:
                    remaining = max(0, remaining - len(items))
                    remaining_connectors = max(1, remaining_connectors - 1)
            except Exception as e:
                stats.failed_sources.append(connector.source_name)
                stats.warnings.append(f"Source {connector.source_name} failed: {e}")
                print(f"[Pipeline] Source {connector.source_name} FAILED: {e}")

        stats.raw_collected = len(all_items)

        saved = []
        with conn.cursor() as cur:
            for item in all_items:
                cur.execute(
                    "SELECT id FROM raw_evidence WHERE source_item_id = %s AND source_type = %s",
                    (item.source_item_id, item.source_type),
                )
                existing = cur.fetchone()
                if existing:
                    continue

                raw_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO raw_evidence
                        (id, collection_run_id, source_type, source_item_id, raw_text,
                         rating, content_hash, source_url, published_at, collected_at, source_metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (
                        raw_id, stats.run_id, item.source_type, item.source_item_id,
                        item.raw_text, item.rating, item.content_hash,
                        item.source_url, item.published_at,
                        json.dumps(item.source_metadata) if item.source_metadata else None,
                    ),
                )
                saved.append({"raw_db_id": raw_id, "item": item})

        conn.commit()
        stats.unique_items = len(saved)
        stats.stage_durations["collect"] = round(time.time() - t0, 2)
        self._complete_stage(conn, stats.run_id, "collect",
                             output_count=len(saved),
                             warnings=stats.warnings[-len(stats.failed_sources):] if stats.failed_sources else None)
        print(f"[Pipeline] Saved {len(saved)} new raw evidence items.")
        return saved

    # ──────────────────────────────────────────────
    # Stage 2-5: Preprocess ALL items, save processed for EVERY item
    # ──────────────────────────────────────────────
    def _preprocess_and_persist(
        self, conn, saved_raw: List[Dict[str, Any]], stats: RunStats
    ) -> List[Dict[str, Any]]:
        """Process every item and persist a processed_evidence row for each, regardless of outcome."""
        # Stages: normalize, mask_pii, deduplicate, relevance_filter
        for stage_key in ["normalize", "mask_pii", "deduplicate", "relevance_filter"]:
            self._start_stage(conn, stats.run_id, stage_key, len(saved_raw))

        self._update_run_status(conn, stats, "running", "normalize")
        t0 = time.time()
        candidates = []

        with conn.cursor() as cur:
            for entry in saved_raw:
                processed = self.preprocessor.process_item(entry["item"])
                status = processed["relevance_status"]
                raw_db_id = entry["raw_db_id"]

                # Separate cleaned and masked text
                cleaned = processed.get("cleaned_text", entry["item"].raw_text)
                masked = processed.get("masked_text", cleaned)

                # The in-memory preprocessor catches duplicates within this run.
                # This lookup extends that guarantee across scheduled runs.
                cur.execute(
                    "SELECT id FROM processed_evidence WHERE canonical_hash = %s AND is_duplicate = FALSE LIMIT 1",
                    (processed.get("canonical_hash"),),
                )
                existing_processed = cur.fetchone()
                duplicate_of = existing_processed[0] if existing_processed else None
                if duplicate_of:
                    processed["is_duplicate"] = True
                    processed["relevance_status"] = "duplicate"

                # Save processed_evidence row for EVERY item
                processed_id = str(uuid.uuid4())
                try:
                    cur.execute(
                        """
                        INSERT INTO processed_evidence
                            (id, raw_evidence_id, cleaned_text, masked_text,
                             language, is_duplicate, duplicate_of, spam_score,
                             relevance_status, processing_version, processed_at,
                             canonical_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            processed_id, raw_db_id, cleaned, masked,
                            processed.get("language", "en"),
                            processed.get("is_duplicate", False),
                            duplicate_of,
                            processed.get("spam_score"),
                            status, PROCESSING_VERSION,
                            processed.get("canonical_hash"),
                        ),
                    )
                except Exception as e:
                    stats.warnings.append(f"Failed to save processed for {raw_db_id}: {e}")
                    continue

                if status == "duplicate":
                    stats.duplicates += 1
                elif status == "noise":
                    stats.noise += 1
                elif status == "candidate_rejected":
                    stats.candidate_rejected += 1
                elif status == "unsupported_language":
                    stats.unsupported_language += 1
                elif status == "pending":
                    stats.candidates_for_ai += 1
                    candidates.append({
                        "raw_db_id": raw_db_id,
                        "processed_id": processed_id,
                        "item": entry["item"],
                        "processed": processed,
                        "cleaned_text": cleaned,
                        "masked_text": masked,
                    })

        conn.commit()
        dur = round(time.time() - t0, 2)
        stats.stage_durations["preprocess"] = dur

        # Complete preprocessing stages
        total = len(saved_raw)
        self._complete_stage(conn, stats.run_id, "normalize", output_count=total)
        self._complete_stage(conn, stats.run_id, "mask_pii", output_count=total)
        self._complete_stage(conn, stats.run_id, "deduplicate",
                             output_count=total - stats.duplicates, rejected_count=stats.duplicates)
        self._complete_stage(conn, stats.run_id, "relevance_filter",
                             output_count=stats.candidates_for_ai,
                             rejected_count=stats.noise + stats.candidate_rejected + stats.unsupported_language)

        print(f"[Pipeline] {stats.candidates_for_ai} candidates passed to AI. "
              f"({stats.duplicates} dupes, {stats.noise} noise, "
              f"{stats.candidate_rejected} rejected, {stats.unsupported_language} non-English)")
        return candidates

    # ──────────────────────────────────────────────
    # Stage 6-7: AI enrichment + span validation, persist ALL fields
    # ──────────────────────────────────────────────
    def _enrich_and_save(
        self, conn, candidates: List[Dict[str, Any]], stats: RunStats
    ):
        self._start_stage(conn, stats.run_id, "ai_extract", len(candidates))
        self._update_run_status(conn, stats, "running", "ai_extract")
        t0 = time.time()

        validations_checked = 0
        validations_valid = 0

        batch_size = 15

        with conn.cursor() as cur:
            for i in range(0, len(candidates), batch_size):
                batch = candidates[i:i + batch_size]

                batch_raw_texts = [entry["masked_text"] for entry in batch]
                batch_masked_texts = [entry["masked_text"] for entry in batch]
                source_type = batch[0]["item"].source_type if batch else "unknown"

                batch_num = i // batch_size + 1
                total_batches = (len(candidates) + batch_size - 1) // batch_size
                print(f"[Pipeline] Processing batch {batch_num}/{total_batches} (size: {len(batch)})")

                # Call AI with bounded retry (max 2 attempts, exponential backoff)
                batch_results = []
                for attempt in range(2):
                    try:
                        batch_results = self.ai.analyze_and_validate_batch(
                            batch_raw_texts=batch_raw_texts,
                            batch_masked_texts=batch_masked_texts,
                            source_type=source_type,
                        )
                        break
                    except Exception as e:
                        print(f"[Pipeline] AI batch attempt {attempt + 1} failed: {e}")
                        if attempt < 1:
                            time.sleep(15 * (attempt + 1))

                # Process each item in the batch against returned results
                for j, entry in enumerate(batch):
                    processed_id = entry["processed_id"]
                    raw_db_id = entry["raw_db_id"]

                    # No result returned for this item
                    if j >= len(batch_results):
                        stats.ai_failure += 1
                        stats.warnings.append(f"AI failed for raw_id {raw_db_id} after 2 attempts.")
                        cur.execute(
                            "UPDATE processed_evidence SET relevance_status='ai_failed' WHERE id=%s",
                            (processed_id,)
                        )
                        continue

                    annotation, span_validation = batch_results[j]

                    if annotation is None:
                        stats.ai_failure += 1
                        stats.warnings.append(f"AI failed for raw_id {raw_db_id} after 2 attempts.")
                        cur.execute(
                            "UPDATE processed_evidence SET relevance_status='ai_failed' WHERE id=%s",
                            (processed_id,)
                        )
                        continue

                    if span_validation:
                        validations_checked += span_validation.get("checked", 0)
                        validations_valid += span_validation.get("valid", 0)

                    # Persist ALL annotation fields
                    try:
                        cur.execute(
                            """
                            INSERT INTO evidence_annotations
                                (id, processed_evidence_id,
                                 wishlist_relevance, reason_for_saving,
                                 wishlist_intent, intent_strength,
                                 purchase_stage, proximity_to_purchase_label,
                                 behaviour_after_saving, revisit_behaviour,
                                 comparison_behaviour, off_platform_research,
                                 information_sought,
                                 workaround, purchase_trigger, abandonment_signal,
                                 contradictory_signal,
                                 frictions, emerging_themes,
                                 conversion_relevance, severity,
                                 segment_signals, evidence_confidence,
                                 supporting_spans, support_span_validation,
                                 annotation_status, analysis_version,
                                 model_provider, model_name,
                                 analysis_notes, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """,
                            (
                                str(uuid.uuid4()), processed_id,
                                annotation.wishlist_relevance,
                                json.dumps(annotation.reason_for_saving),
                                annotation.wishlist_intent,
                                annotation.intent_strength,
                                annotation.purchase_stage,
                                annotation.proximity_to_purchase,
                                json.dumps(annotation.behaviour_after_saving),
                                annotation.revisit_behaviour,
                                annotation.comparison_behaviour,
                                json.dumps(annotation.off_platform_research),
                                json.dumps(annotation.information_sought),
                                json.dumps(annotation.workaround),
                                json.dumps(annotation.purchase_trigger),
                                json.dumps(annotation.abandonment_signal),
                                annotation.contradictory_signal,
                                json.dumps([f.model_dump() for f in annotation.frictions]),
                                json.dumps(annotation.emerging_themes),
                                annotation.conversion_relevance,
                                max((f.severity for f in annotation.frictions), default=0),
                                json.dumps(annotation.segment_signals),
                                annotation.evidence_confidence,
                                json.dumps([s.model_dump() for s in annotation.supporting_spans]),
                                json.dumps(span_validation) if span_validation else None,
                                "ai_generated", ANALYSIS_VERSION,
                                "gemini", self.model_name,
                                annotation.analysis_notes,
                            ),
                        )
                        stats.ai_success += 1

                        # Update processed_evidence status
                        rel_status = "ai_retained" if annotation.wishlist_relevance in ("high", "medium") else "ai_not_relevant"
                        cur.execute(
                            "UPDATE processed_evidence SET relevance_status=%s WHERE id=%s",
                            (rel_status, processed_id)
                        )

                    except Exception as e:
                        stats.ai_failure += 1
                        stats.warnings.append(f"Failed to save annotation for {raw_db_id}: {e}")

                # Sleep 4s between batches to avoid hitting rate limits (15 req/min on free tier)
                if i + batch_size < len(candidates):
                    time.sleep(4)

        conn.commit()
        dur = round(time.time() - t0, 2)
        stats.stage_durations["ai_extract"] = dur
        self._complete_stage(conn, stats.run_id, "ai_extract",
                             output_count=stats.ai_success, rejected_count=stats.ai_failure)

        # Validate stage
        self._start_stage(conn, stats.run_id, "validate_evidence", validations_checked)
        self._complete_stage(conn, stats.run_id, "validate_evidence",
                             output_count=validations_valid,
                             rejected_count=validations_checked - validations_valid)

        print(f"[Pipeline] AI success={stats.ai_success} | failure={stats.ai_failure} | "
              f"spans validated={validations_valid}/{validations_checked}")



    # ──────────────────────────────────────────────
    # Stage 8-9: Aggregate, rank, and complete the run
    # ──────────────────────────────────────────────
    def _aggregate_and_rank(self, conn, stats: RunStats) -> int:
        """Build current opportunity hypotheses and persist their score breakdowns."""
        self._start_stage(conn, stats.run_id, "aggregate", stats.ai_success)
        self._update_run_status(conn, stats, "running", "aggregate")
        try:
            aggregator = Aggregator(self.db_url)
            annotations = aggregator._fetch_annotations(conn)
            segments = SegmentFinder().find_segments(annotations)
            candidates = OpportunityGenerator().generate(segments, annotations)
            self._complete_stage(conn, stats.run_id, "aggregate", output_count=len(candidates))

            self._start_stage(conn, stats.run_id, "rank_opportunities", len(candidates))
            self._update_run_status(conn, stats, "running", "rank_opportunities")
            usable_sources = max(1, len({a.get("source_type") for a in annotations if a.get("source_type")}))
            ranked = Ranker().rank(candidates, annotations, len(annotations), usable_source_count=usable_sources)
            version = f"{RANKING_VERSION}:{stats.run_id}"

            with conn.cursor() as cur:
                cur.execute("DELETE FROM opportunity_evidence WHERE opportunity_id IN (SELECT id FROM opportunities WHERE opportunity_version = %s)", (version,))
                cur.execute("DELETE FROM opportunities WHERE opportunity_version = %s", (version,))
                for opportunity in ranked:
                    opportunity_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"myntra:{version}:{opportunity.id}"))
                    cur.execute(
                        """
                        INSERT INTO opportunities
                            (id, title, problem_pattern, behavioural_segment,
                             frequency_score, severity_score, intent_score,
                             conversion_relevance_score, source_convergence_score,
                             segment_concentration_score, evidence_confidence_score,
                             overall_score, evidence_count, source_count, status,
                             opportunity_version, opportunity_statement, dominant_friction,
                             affected_journey_stage, confidence_label, score_version,
                             taxonomy_version, generated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, 'candidate', %s, %s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            opportunity_id,
                            opportunity.statement[:160],
                            opportunity.statement,
                            opportunity.segment_name,
                            opportunity.score_frequency,
                            opportunity.score_severity,
                            opportunity.score_purchase_intent,
                            opportunity.score_conversion_relevance,
                            opportunity.score_source_convergence,
                            opportunity.score_segment_concentration,
                            opportunity.score_evidence_confidence,
                            opportunity.overall_score,
                            opportunity.evidence_count,
                            usable_sources,
                            version,
                            opportunity.statement,
                            opportunity.dominant_friction_type,
                            opportunity.dominant_purchase_stage,
                            "high" if opportunity.overall_score >= 0.67 else "medium",
                            RANKING_VERSION,
                            "v2.0.0",
                        ),
                    )

                    segment_annotations = OpportunityGenerator()._get_segment_annotations(
                        next((s for s in segments if s.name == opportunity.segment_name), segments[0] if segments else None),
                        annotations,
                    ) if segments else []
                    for annotation in segment_annotations:
                        annotation_id = annotation.get("annotation_id")
                        if not annotation_id:
                            continue
                        cur.execute(
                            """
                            INSERT INTO opportunity_evidence
                                (opportunity_id, annotation_id, support_strength, relationship_type)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (opportunity_id, annotation_id) DO NOTHING
                            """,
                            (opportunity_id, annotation_id, 2, "supports"),
                        )
            conn.commit()
            self._complete_stage(conn, stats.run_id, "rank_opportunities", output_count=len(ranked))
            return len(ranked)
        except Exception as exc:
            stats.warnings.append(f"Aggregation/ranking failed: {exc}")
            self._complete_stage(conn, stats.run_id, "aggregate", error=str(exc))
            self._complete_stage(conn, stats.run_id, "rank_opportunities", error=str(exc))
            return 0

    def _complete_run(self, conn, stats: RunStats):
        self._aggregate_and_rank(conn, stats)
        status = "completed" if not stats.warnings else "completed_with_warnings"

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE collection_runs
                SET status=%s, completed_at=NOW(),
                    items_collected=%s, items_retained=%s,
                    items_unique=%s, items_processed=%s,
                    items_relevant=%s,
                    items_ai_attempted=%s, items_ai_succeeded=%s, items_ai_failed=%s,
                    successful_sources=%s, failed_sources=%s,
                    warnings=%s, current_stage='completed', progress_percent=100
                WHERE id=%s
                """,
                (
                    status, stats.raw_collected, stats.items_retained(),
                    stats.unique_items, stats.unique_items, stats.ai_success,
                    stats.candidates_for_ai, stats.ai_success, stats.ai_failure,
                    json.dumps(stats.successful_sources),
                    json.dumps(stats.failed_sources),
                    json.dumps(stats.warnings) if stats.warnings else None,
                    stats.run_id,
                ),
            )
        conn.commit()
        print(f"[Pipeline] Run {stats.run_id} finished: {status}")

    # ──────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────
    def run(
        self,
        connectors: List[SourceConnector],
        run_type: str = "manual",
        dataset_scope: str = "fresh_sample",
        requested_sources: List[str] = None,
        item_cap: int = None,
        run_id: str = None,
    ) -> RunStats:
        stats = RunStats(run_type=run_type, dataset_scope=dataset_scope)
        if run_id:
            stats.run_id = run_id
        
        conn = self._get_conn()

        try:
            # Check if run already exists in DB (e.g. created by API)
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM collection_runs WHERE id = %s", (stats.run_id,))
                exists = cur.fetchone()
            
            if exists:
                # Setup stages but don't re-insert run
                with conn.cursor() as cur:
                    for seq, (key, label) in enumerate(STAGE_KEYS, 1):
                        cur.execute(
                            """
                            INSERT INTO collection_run_stages
                                (id, run_id, sequence_number, stage_key, stage_label, status)
                            VALUES (%s, %s, %s, %s, %s, 'pending')
                            ON CONFLICT (run_id, stage_key) DO NOTHING
                            """,
                            (str(uuid.uuid4()), stats.run_id, seq, key, label),
                        )
                conn.commit()
                self._update_run_status(conn, stats, "running")
            else:
                self._create_run(conn, stats, requested_sources=requested_sources, item_cap=item_cap)
            
            saved_raw = self._collect_and_save_raw(conn, connectors, stats, item_cap=item_cap)
            candidates = self._preprocess_and_persist(conn, saved_raw, stats)
            self._enrich_and_save(conn, candidates, stats)
            self._complete_run(conn, stats)
        except Exception as e:
            stats.warnings.append(f"Pipeline fatal error: {e}")
            print(f"[Pipeline] FATAL: {e}")
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE collection_runs SET status='failed', error_summary=%s WHERE id=%s",
                        (str(e), stats.run_id),
                    )
                conn.commit()
            except Exception:
                pass
        finally:
            conn.close()

        # Print final summary
        print("\n" + "="*50)
        print(f"  Pipeline Run Summary — {stats.run_id}")
        print("="*50)
        print(f"  Scope:               {stats.dataset_scope}")
        print(f"  Raw collected:       {stats.raw_collected}")
        print(f"  Unique (new):        {stats.unique_items}")
        print(f"  Duplicates:          {stats.duplicates}")
        print(f"  Noise/spam dropped:  {stats.noise}")
        print(f"  Candidate rejected:  {stats.candidate_rejected}")
        print(f"  Non-English:         {stats.unsupported_language}")
        print(f"  Sent to AI:          {stats.candidates_for_ai}")
        print(f"  AI success:          {stats.ai_success}")
        print(f"  AI failure:          {stats.ai_failure}")
        print(f"  Sources OK:          {stats.successful_sources}")
        print(f"  Sources failed:      {stats.failed_sources}")
        print(f"  Stage durations:     {stats.stage_durations}")
        if stats.warnings:
            print(f"  Warnings ({len(stats.warnings)}):")
            for w in stats.warnings:
                print(f"    - {w}")
        print("="*50 + "\n")

        return stats
