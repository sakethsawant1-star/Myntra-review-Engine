from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

class CollectionRun(BaseModel):
    id: UUID
    run_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    source_config_version: Optional[str] = None
    items_collected: int = 0
    items_retained: int = 0
    error_summary: Optional[str] = None

class RawEvidence(BaseModel):
    id: UUID
    source_type: str
    source_item_id: str
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: datetime
    raw_text: str
    rating: Optional[float] = None
    source_metadata: Optional[Dict[str, Any]] = None
    content_hash: str
    collection_run_id: Optional[UUID] = None

class ProcessedEvidence(BaseModel):
    id: UUID
    raw_evidence_id: UUID
    cleaned_text: Optional[str] = None
    masked_text: Optional[str] = None
    language: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[UUID] = None
    spam_score: Optional[float] = None
    relevance_status: Optional[str] = None
    relevance_score: Optional[float] = None
    processing_version: Optional[str] = None

class Friction(BaseModel):
    type: str
    label: str
    severity: int
    support_span: str

class EvidenceAnnotation(BaseModel):
    id: UUID
    processed_evidence_id: UUID
    analysis_version: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    wishlist_relevance: Optional[str] = None
    reason_for_saving: Optional[str] = None
    wishlist_intent: Optional[str] = None
    purchase_stage: Optional[str] = None
    behaviour_after_saving: Optional[List[str]] = None
    revisit_behaviour: Optional[str] = None
    comparison_behaviour: Optional[str] = None
    off_platform_research: Optional[List[str]] = None
    workaround: Optional[str] = None
    purchase_trigger: Optional[str] = None
    abandonment_signal: Optional[str] = None
    frictions: Optional[List[Friction]] = None
    emerging_themes: Optional[List[str]] = None
    intent_strength: Optional[int] = None
    severity: Optional[int] = None
    conversion_relevance: Optional[int] = None
    proximity_to_purchase: Optional[int] = None
    segment_signals: Optional[Dict[str, Any]] = None
    evidence_confidence: Optional[int] = None
    supporting_spans: Optional[Dict[str, str]] = None
    analysis_notes: Optional[str] = None

class Opportunity(BaseModel):
    id: UUID
    title: str
    problem_pattern: Optional[str] = None
    behavioural_segment: Optional[str] = None
    frequency_score: Optional[float] = None
    severity_score: Optional[float] = None
    intent_score: Optional[float] = None
    conversion_relevance_score: Optional[float] = None
    source_convergence_score: Optional[float] = None
    segment_concentration_score: Optional[float] = None
    evidence_confidence_score: Optional[float] = None
    overall_score: Optional[float] = None
    evidence_count: int = 0
    source_count: int = 0
    status: Optional[str] = None
    opportunity_version: Optional[str] = None

class OpportunityEvidence(BaseModel):
    opportunity_id: UUID
    annotation_id: UUID
    support_strength: Optional[int] = None
    relationship_type: Optional[str] = None
