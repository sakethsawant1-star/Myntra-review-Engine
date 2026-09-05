# Myntra Project Decisions

This document tracks all significant decisions made during the implementation of the Myntra Wishlist AI Discovery Engine.

## Phase 0: Project Bootstrap
- **Date**: 2026-08-26
- **Decision**: Initialize the base project structure and Git repository.
- **Context**: The foundational structure was set up according to the `architecture.md` and `implementation plan.md`. Documentation files were retained in the existing `Docs/` directory. Placeholder configurations (`taxonomy.yaml`, `ranking.yaml`, `sources.yaml`) were created.

## Phase 1: Database Schema and Evidence Contracts
- **Date**: 2026-08-26
- **Decision**: Define strict separation between raw and processed evidence in the database layout.
- **Context**: SQL migrations (`0001_initial_schema.sql`) and Pydantic models (`models.py`) were created to ensure source text remains immutable, and AI output/human overrides are tracked separately. A seed data file was created reflecting the required edge-cases (low intent, cross-platform comparison, contradictory evidence) without biasing heavily toward one root cause.

## Phase 2: Source Connector Foundation
- **Date**: 2026-08-26
- **Decision**: Build Google Play, Apple App Store, and Reddit connectors in Phase 2 (Priority A + B), deferring YouTube and URL importer to Phase C.
- **Context**: All connectors implement the common `SourceConnector` abstract base class and output normalized `RawEvidenceItem` objects. Scrapers use public APIs only (`google-play-scraper`, `app-store-scraper`, official Reddit PRAW). The `app-store-scraper` library pins `requests==2.23.0`; this was pinned up then restored to `>=2.32.2` to avoid breaking other dependencies. All 10 connector unit tests pass.

## Phase 3: Deterministic Preprocessing Pipeline
- **Date**: 2026-08-26
- **Decision**: Use deterministic regex for PII masking (phones, emails, order numbers) instead of downloading large Spacy/Presidio language models. Use `langdetect` for language classification.
- **Context**: A lightweight regex approach keeps the backend container size small while effectively masking the specific PII risks (contact info, order tracking numbers) found in Myntra reviews. The `Preprocessor` class filters noise, deduplicates hashes in-memory for the current batch, and assigns a `pending` relevance status to items that pass the fast Stage-A keyword filter. Unit tests (6/6) confirm standardizing and deduplication logic.

## Phase 4: AI Analysis Schema & Prompts
- **Date**: 2026-08-26
- **Decision**: Use Gemini 1.5 Flash via `google-generativeai` utilizing native `response_schema` strict JSON enforcement.
- **Context**: To prevent AI hallucination, the Pydantic schema `AIAnnotation` strictly enforces `Literal` choices including `unclear` and `not_applicable` for every behavioral field. The prompt explicitly commands the AI not to guess demographic data or solutionize features. Unit tests confirm that the Gemini output perfectly maps to the Pydantic models.

## Phase 5: End-to-End Pipeline
- **Date**: 2026-08-26
- **Decision**: Run the pipeline as a single synchronous Python process (not async/serverless) for now.
- **Context**: The pipeline has 9 stages with full idempotency (DB-level dedup by source_item_id), bounded AI retries (max 2), graceful failure isolation per item, and a final run summary. The architecture is ready to be moved to a Railway background worker in Phase 7 if execution times are too long for serverless.

## Phase 6: Aggregation, Segments, Opportunity Ranking
- **Date**: 2026-08-26
- **Decision**: All segments are rule-based (no AI) and require a minimum of 2 evidence items before promotion. Ranking uses 6 configurable dimensions from `ranking.yaml`.
- **Context**: Four initial segments discovered: `high_intent_blocked`, `cross_platform_researchers`, `passive_bookmarkers`, `price_sensitive_waiters`. All score outputs store both the overall score AND every component score for auditability. Duplicate evidence cannot inflate frequency because deduplication is enforced at the pipeline level. All 7 tests pass.

## Phase 7: Backend API & Hosting Decision
- **Date**: 2026-08-26
- **Decision**: Select **Path B (Railway FastAPI worker)** instead of Vercel Serverless.
- **Context**: Implemented FastAPI routers (`/api/dashboard`, `/api/opportunities`, `/api/pipeline`). Because Gemini Flash averages 1-3 seconds per request, processing a standard batch of 100-200 reviews will take 3-10 minutes. This vastly exceeds standard serverless function timeouts (10s - 60s). Therefore, a persistent Python backend (like Railway or Render) is structurally required for the pipeline worker.

## Phase 8: Discovery Dashboard (Frontend)
- **Date**: 2026-09-02
- **Decision**: Implemented an evaluator-facing Single Page Web Dashboard in `frontend/` using Vanilla HTML5, CSS3, and JavaScript, directly served by FastAPI.
- **Context**: The dashboard features 6 interactive views: Overview (metrics & source distribution), Behaviour Explorer (intent, stage, friction, off-platform breakdown with count/denominator auditability), Segment Explorer (explainable candidate segments), Opportunity Board (multi-dimensional ranker output with component score breakdowns), Evidence Drill-Down (search/filter masked evidence by source or friction), and Pipeline Monitor (real-time 9-stage workflow status). Incorporates seamless offline demo-mode fallbacks if backend APIs are offline.
