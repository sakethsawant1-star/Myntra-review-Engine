-- 0002_engine_refinement.sql
-- Additive migration: no destructive changes to existing tables.
-- Adds columns, tables, and indexes required by the ANTIGRAVITY refinement spec.

-- ================================================================
-- 1. Refine collection_runs
-- ================================================================
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS dataset_scope TEXT DEFAULT 'manual';
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS requested_item_cap INTEGER;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS requested_sources JSONB;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS enabled_sources JSONB;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS successful_sources JSONB;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS failed_sources JSONB;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS current_stage TEXT;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS progress_percent REAL DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_unique INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_processed INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_relevant INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_ai_attempted INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_ai_succeeded INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_ai_failed INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS items_human_reviewed INTEGER DEFAULT 0;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS model_provider TEXT;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS model_name TEXT;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS analysis_version TEXT;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS processing_version TEXT;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS ranking_version TEXT;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS warnings JSONB;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS requested_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE collection_runs ADD COLUMN IF NOT EXISTS heartbeat_at TIMESTAMP WITH TIME ZONE;

-- Keep the bundled development seed visible to the default dashboard scope.
UPDATE collection_runs
SET dataset_scope = 'fresh_sample'
WHERE run_type = 'manual' AND (dataset_scope IS NULL OR dataset_scope = 'manual');

-- ================================================================
-- 2. New table: collection_run_stages
-- ================================================================
CREATE TABLE IF NOT EXISTS collection_run_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES collection_runs(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    stage_key TEXT NOT NULL,
    stage_label TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    input_count INTEGER DEFAULT 0,
    output_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    warnings JSONB,
    error_message TEXT,
    metadata JSONB,
    UNIQUE (run_id, stage_key)
);

CREATE INDEX IF NOT EXISTS idx_run_stages_run_id ON collection_run_stages(run_id);

-- ================================================================
-- 3. Refine processed_evidence
-- ================================================================
-- cleaned_text already exists; ensure masked_text is separate
-- masked_text column already exists in 0001 schema, but add if missing
ALTER TABLE processed_evidence ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE processed_evidence ADD COLUMN IF NOT EXISTS canonical_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_processed_evidence_raw_id ON processed_evidence(raw_evidence_id);
CREATE INDEX IF NOT EXISTS idx_processed_evidence_relevance ON processed_evidence(relevance_status);

-- ================================================================
-- 4. Refine evidence_annotations
-- ================================================================
-- Many of these columns exist in 0001 but may not be populated.
-- Add any that are missing.
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS reason_for_saving JSONB;
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS information_sought JSONB;
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS purchase_trigger TEXT;
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS abandonment_signal TEXT;
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS contradictory_signal TEXT;
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS support_span_validation JSONB;
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS annotation_status TEXT DEFAULT 'ai_generated';
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Ensure behaviour_after_saving is JSONB (it is in 0001)
-- Ensure frictions is JSONB (it is in 0001)
-- Ensure emerging_themes is JSONB (it is in 0001)
-- Ensure supporting_spans is JSONB (it is in 0001)
-- Ensure segment_signals is JSONB (it is in 0001)
-- Ensure off_platform_research is JSONB (it is in 0001)

-- Fix proximity_to_purchase: was INTEGER in 0001 but should be TEXT
-- We cannot ALTER column type if data exists, so add a new column
ALTER TABLE evidence_annotations ADD COLUMN IF NOT EXISTS proximity_to_purchase_label TEXT;

CREATE INDEX IF NOT EXISTS idx_annotations_processed_id ON evidence_annotations(processed_evidence_id);
CREATE INDEX IF NOT EXISTS idx_annotations_intent ON evidence_annotations(wishlist_intent);
CREATE INDEX IF NOT EXISTS idx_annotations_stage ON evidence_annotations(purchase_stage);
CREATE INDEX IF NOT EXISTS idx_annotations_confidence ON evidence_annotations(evidence_confidence);
CREATE INDEX IF NOT EXISTS idx_raw_evidence_run_id ON raw_evidence(collection_run_id);

-- ================================================================
-- 5. Refine opportunities
-- ================================================================
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS opportunity_statement TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS dominant_friction TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS affected_journey_stage TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS contradiction_count INTEGER DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS adjacent_evidence_count INTEGER DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS strongest_source_share REAL;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS confidence_label TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS score_version TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS taxonomy_version TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update status column to have a default
-- (status already exists in 0001)

-- ================================================================
-- 6. Add research_question_coverage table
-- ================================================================
CREATE TABLE IF NOT EXISTS research_question_coverage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES collection_runs(id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    fields_used JSONB,
    evidence_count INTEGER DEFAULT 0,
    corpus_denominator INTEGER DEFAULT 0,
    coverage_percent REAL DEFAULT 0,
    top_signal TEXT,
    confidence TEXT,
    limitation TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- 7. Optional: survey_snapshots table
-- ================================================================
CREATE TABLE IF NOT EXISTS survey_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_version TEXT NOT NULL,
    total_responses INTEGER DEFAULT 0,
    eligible_base INTEGER DEFAULT 0,
    aggregates JSONB NOT NULL,
    data_quality_notes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
