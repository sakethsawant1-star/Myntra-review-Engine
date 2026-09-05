-- 0001_initial_schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE collection_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_type TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL,
    source_config_version TEXT,
    items_collected INTEGER DEFAULT 0,
    items_retained INTEGER DEFAULT 0,
    error_summary TEXT
);

CREATE TABLE raw_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    source_url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_text TEXT NOT NULL,
    rating REAL,
    source_metadata JSONB,
    content_hash TEXT NOT NULL,
    collection_run_id UUID REFERENCES collection_runs(id),
    UNIQUE (source_type, source_item_id)
);

CREATE TABLE processed_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_evidence_id UUID NOT NULL REFERENCES raw_evidence(id) ON DELETE CASCADE,
    cleaned_text TEXT,
    masked_text TEXT,
    language TEXT,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES processed_evidence(id),
    spam_score REAL,
    relevance_status TEXT,
    relevance_score REAL,
    processing_version TEXT
);

CREATE TABLE evidence_annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    processed_evidence_id UUID NOT NULL REFERENCES processed_evidence(id) ON DELETE CASCADE,
    analysis_version TEXT,
    model_provider TEXT,
    model_name TEXT,
    wishlist_relevance TEXT,
    reason_for_saving TEXT,
    wishlist_intent TEXT,
    purchase_stage TEXT,
    behaviour_after_saving JSONB,
    revisit_behaviour TEXT,
    comparison_behaviour TEXT,
    off_platform_research JSONB,
    workaround TEXT,
    purchase_trigger TEXT,
    abandonment_signal TEXT,
    frictions JSONB,
    emerging_themes JSONB,
    intent_strength INTEGER,
    severity INTEGER,
    conversion_relevance INTEGER,
    proximity_to_purchase INTEGER,
    segment_signals JSONB,
    evidence_confidence INTEGER,
    supporting_spans JSONB,
    analysis_notes TEXT
);

CREATE TABLE human_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    annotation_id UUID NOT NULL REFERENCES evidence_annotations(id) ON DELETE CASCADE,
    review_status TEXT NOT NULL,
    field_overrides JSONB,
    review_note TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    problem_pattern TEXT,
    behavioural_segment TEXT,
    frequency_score REAL,
    severity_score REAL,
    intent_score REAL,
    conversion_relevance_score REAL,
    source_convergence_score REAL,
    segment_concentration_score REAL,
    evidence_confidence_score REAL,
    overall_score REAL,
    evidence_count INTEGER DEFAULT 0,
    source_count INTEGER DEFAULT 0,
    status TEXT,
    opportunity_version TEXT
);

CREATE TABLE opportunity_evidence (
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    annotation_id UUID NOT NULL REFERENCES evidence_annotations(id) ON DELETE CASCADE,
    support_strength INTEGER,
    relationship_type TEXT,
    PRIMARY KEY (opportunity_id, annotation_id)
);
