# Myntra Wishlist AI Discovery Engine - Architecture

## 1. Purpose of This Document

This document defines the technical architecture for the **Myntra Wishlist AI Discovery Engine** described in `problem statement.md`.

It is an implementation architecture for the discovery engine only. It does not define the final graduation-project solution or MVP.

The engine must remain research-neutral. It should help us discover and compare behavioural opportunities that may affect Myntra's 30-day wishlist-to-purchase conversion without hard-coding a preferred problem such as price, fit, size, reviews, styling, or any future feature idea.

---

## 2. Architecture Goals

The architecture must support the following product and engineering goals:

1. Collect public user conversations from multiple relevant sources.
2. Preserve source metadata and original evidence for auditability.
3. Clean, deduplicate, mask PII, and filter irrelevant content.
4. Use AI to convert unstructured conversation into structured behavioural evidence.
5. Allow new themes and behaviours to emerge instead of forcing every item into a fixed taxonomy.
6. Separate AI interpretation from deterministic calculations and ranking logic.
7. Aggregate evidence into behavioural patterns, segment signals, and opportunity areas.
8. Rank opportunities using more than mention volume.
9. Let a human inspect the underlying evidence behind every important insight.
10. Expose the engine through a deployed, testable web interface.
11. Support both scheduled full-corpus analysis and a small real-time evaluator/demo run.
12. Keep sources, prompts, models, taxonomy, and ranking weights configurable.
13. Avoid claiming causal impact from public conversation alone.

---

## 3. High-Level System Architecture

```text
                     PUBLIC DATA SOURCES
                            |
        +-------------------+-------------------+
        |                   |                   |
   Google Play          Apple App Store      Reddit
        |                   |                   |
        +-----------+-------+----------+--------+
                    |                  |
                 YouTube        Approved public
                 comments        forums / URL import
                    |                  |
                    +--------+---------+
                             |
                    [1] SOURCE CONNECTORS
                             |
                             v
                    [2] RAW INGESTION LAYER
                             |
                       Raw Evidence Store
                             |
                             v
                    [3] PREPROCESSING LAYER
                  Normalize / Language / PII
                   Spam / Dedup / Relevance
                             |
                             v
                    [4] AI ENRICHMENT LAYER
                 Behaviour + Intent + Friction
                 Workaround + Stage + Evidence
                             |
                             v
                   [5] STRUCTURED EVIDENCE DB
                             |
               +-------------+-------------+
               |                           |
               v                           v
       [6] AGGREGATION ENGINE       [7] HUMAN REVIEW
       Counts / cross-source         Inspect evidence
       patterns / segments          flag / override
               |                           |
               +-------------+-------------+
                             |
                             v
                 [8] OPPORTUNITY ENGINE
             Synthesis + transparent ranking
                             |
                             v
                      [9] BACKEND API
                             |
                             v
                      [10] DASHBOARD
             Findings / filters / evidence drilldown
                             |
                             v
                 PRODUCT RESEARCH DECISION
      Opportunities -> target segment -> interviews
```

---

## 4. Proposed Technology Stack

The stack is intentionally simple, deployable, and familiar enough to build quickly while remaining production-like.

### 4.1 Frontend

**Recommended:** Next.js / React hosted on Vercel

Responsibilities:

- Discovery dashboard
- Pipeline status
- Source and evidence filters
- Opportunity comparison
- Evidence drill-down
- Human-review controls
- Small "Run Fresh Sample" evaluator action

Why:

- Fast deployment
- Easy public URL
- Good chart/table ecosystem
- Simple API integration
- Good fit for an evaluator-facing web application

### 4.2 Backend API

**Recommended:** Python FastAPI hosted on Railway

Responsibilities:

- Source connector orchestration
- Pipeline jobs
- Preprocessing
- AI enrichment
- Aggregation
- Opportunity scoring
- Dashboard API
- Human-review endpoints

Why Python:

- Strong scraping/data-processing ecosystem
- Easy Pydantic schema validation for LLM JSON
- Good text-processing libraries
- FastAPI provides clear typed endpoints and automatic docs

### 4.3 Database

**Recommended:** Supabase PostgreSQL

Responsibilities:

- Raw evidence metadata
- Cleaned evidence
- AI annotations
- pipeline/job state
- opportunities and scores
- human-review decisions
- taxonomy/prompt versions

Optional extensions:

- `pgvector` if semantic deduplication or evidence clustering requires embeddings
- Supabase Storage only if source snapshots become too large for normal database storage

### 4.4 AI Layer

Use a provider abstraction so the model can be changed without changing the rest of the pipeline.

Initial candidates:

- Gemini
- Groq-hosted open models

The final provider will be selected during implementation based on structured-output reliability, latency, rate limits, and cost.

The engine must not depend on provider-specific fields outside the AI adapter.

### 4.5 Scheduling

**Recommended:** GitHub Actions for scheduled full runs plus backend jobs for small interactive runs.

- Nightly / manual full-corpus job: GitHub Actions calls the backend pipeline endpoint or executes the pipeline worker.
- Evaluator "Run Fresh Sample": backend starts a capped real pipeline job using a small number of recent items.

This prevents the dashboard from pretending that a pipeline ran when it only displayed simulated logs.

---

## 5. Repository / Project Structure

Recommended structure:

```text
myntra-grad-project/
|
+-- problem statement.md
+-- architecture.md
+-- implementation plan.md
+-- README.md
|
+-- backend/
|   +-- app/
|   |   +-- main.py
|   |   +-- api/
|   |   |   +-- dashboard.py
|   |   |   +-- evidence.py
|   |   |   +-- opportunities.py
|   |   |   +-- pipeline.py
|   |   |   +-- review.py
|   |   |
|   |   +-- connectors/
|   |   |   +-- base.py
|   |   |   +-- google_play.py
|   |   |   +-- apple_store.py
|   |   |   +-- reddit.py
|   |   |   +-- youtube.py
|   |   |   +-- url_import.py
|   |   |
|   |   +-- pipeline/
|   |   |   +-- ingest.py
|   |   |   +-- preprocess.py
|   |   |   +-- deduplicate.py
|   |   |   +-- relevance.py
|   |   |   +-- enrich.py
|   |   |   +-- aggregate.py
|   |   |   +-- opportunities.py
|   |   |
|   |   +-- ai/
|   |   |   +-- provider.py
|   |   |   +-- prompts.py
|   |   |   +-- schemas.py
|   |   |   +-- validators.py
|   |   |
|   |   +-- scoring/
|   |   |   +-- opportunity_score.py
|   |   |   +-- rubrics.py
|   |   |
|   |   +-- db/
|   |   |   +-- models.py
|   |   |   +-- repository.py
|   |   |
|   |   +-- config/
|   |       +-- taxonomy.yaml
|   |       +-- ranking.yaml
|   |       +-- sources.yaml
|   |
|   +-- tests/
|   +-- requirements.txt
|   +-- Dockerfile
|
+-- frontend/
|   +-- app/
|   +-- components/
|   +-- lib/
|   +-- public/
|   +-- package.json
|
+-- database/
|   +-- migrations/
|   +-- seed/
|
+-- research/
|   +-- validation_set/
|   +-- human_review/
|
+-- .github/
    +-- workflows/
        +-- nightly-pipeline.yml
```

The exact folder names may change during implementation, but the separation of concerns should remain.

---

## 6. Source Connector Architecture

### 6.1 Connector Interface

Every source should implement one common interface so new sources can be added without changing the analysis pipeline.

Conceptual interface:

```python
class SourceConnector:
    source_name: str

    def collect(self, since=None, limit=None) -> list[RawEvidence]:
        ...
```

Each connector outputs the same normalized raw-evidence object.

### 6.2 Initial Sources

#### Google Play Store

Collect public Myntra app reviews with:

- review text
- rating
- date
- app version where available
- stable source identifier

#### Apple App Store

Collect public Myntra app reviews with equivalent metadata where available.

#### Reddit

Use official or permitted public-access methods.

Collect relevant posts/comments from queries and communities connected to:

- Myntra
- fashion shopping
- wishlists / saved items
- online apparel purchase decisions
- comparisons / fit / sizing / trust / purchase hesitation

Search terms are discovery seeds, not labels for final findings.

#### YouTube

Use the YouTube Data API where available.

Collect comments from relevant public videos about Myntra and online fashion shopping when the comments contain product-decision evidence.

#### Approved public forums / URL importer

Provide a controlled URL-import connector for public pages that are technically and legally accessible.

The engine must not bypass authentication, anti-bot controls, paywalls, or other access restrictions.

### 6.3 Source Metadata

Every item should retain:

- `source_type`
- `source_item_id`
- `source_url` where permissible
- `published_at`
- `collected_at`
- `rating` where applicable
- `parent_context` where needed
- `collection_run_id`

Author/user identifiers should not be exposed to the public dashboard.

---

## 7. Data Model

The architecture separates **raw evidence**, **processed evidence**, and **AI interpretation** so all important conclusions remain auditable.

### 7.1 `collection_runs`

Tracks each ingestion run.

Important fields:

- `id`
- `run_type` - scheduled / manual / evaluator_sample
- `started_at`
- `completed_at`
- `status`
- `source_config_version`
- `items_collected`
- `items_retained`
- `error_summary`

### 7.2 `raw_evidence`

Immutable source record.

Important fields:

- `id`
- `source_type`
- `source_item_id`
- `source_url`
- `published_at`
- `collected_at`
- `raw_text`
- `rating`
- `source_metadata` JSONB
- `content_hash`
- `collection_run_id`

Raw evidence is never directly returned by the public dashboard unless sanitized.

### 7.3 `processed_evidence`

Deterministically processed version.

Important fields:

- `id`
- `raw_evidence_id`
- `cleaned_text`
- `masked_text`
- `language`
- `is_duplicate`
- `duplicate_of`
- `spam_score`
- `relevance_status`
- `relevance_score`
- `processing_version`

### 7.4 `evidence_annotations`

Structured AI interpretation.

Important fields:

- `id`
- `processed_evidence_id`
- `analysis_version`
- `model_provider`
- `model_name`
- `wishlist_relevance`
- `reason_for_saving`
- `wishlist_intent`
- `purchase_stage`
- `behaviour_after_saving`
- `revisit_behaviour`
- `comparison_behaviour`
- `off_platform_research`
- `workaround`
- `purchase_trigger`
- `abandonment_signal`
- `frictions` JSONB array
- `emerging_themes` JSONB array
- `intent_strength`
- `severity`
- `conversion_relevance`
- `proximity_to_purchase`
- `segment_signals` JSONB
- `evidence_confidence`
- `supporting_spans` JSONB
- `analysis_notes`

### 7.5 `human_reviews`

Stores manual QA and overrides.

Important fields:

- `id`
- `annotation_id`
- `review_status` - accepted / flagged / corrected
- `field_overrides` JSONB
- `review_note`
- `reviewed_at`

Human overrides never destroy the original model output.

### 7.6 `opportunities`

Stores synthesized opportunity areas.

Important fields:

- `id`
- `title`
- `problem_pattern`
- `behavioural_segment`
- `frequency_score`
- `severity_score`
- `intent_score`
- `conversion_relevance_score`
- `source_convergence_score`
- `segment_concentration_score`
- `evidence_confidence_score`
- `overall_score`
- `evidence_count`
- `source_count`
- `status`
- `opportunity_version`

### 7.7 `opportunity_evidence`

Many-to-many mapping between opportunities and supporting evidence.

Fields:

- `opportunity_id`
- `annotation_id`
- `support_strength`
- `relationship_type` - supports / contradicts / adjacent

This is important because the dashboard must show both supporting and contradictory evidence.

---

## 8. Preprocessing Pipeline

Preprocessing must be primarily deterministic.

### 8.1 Normalization

Actions:

- normalize whitespace
- remove HTML markup where applicable
- normalize repeated punctuation
- preserve meaningful emojis where useful
- preserve original text separately

### 8.2 Language Handling

- Detect language.
- Keep English evidence directly.
- For supported non-English evidence, store original text and optionally create a translated analysis text.
- Never replace the original source evidence with translation.

### 8.3 PII Masking

Mask obvious personal identifiers from the text exposed to AI/public dashboard where appropriate:

- phone numbers
- email addresses
- addresses
- order/account identifiers
- other obvious personal data

Public usernames are not needed for analysis and should not be displayed.

### 8.4 Spam / Noise Filtering

Remove or down-rank content such as:

- empty reviews
- promotional spam
- repeated copy-paste complaints
- content unrelated to shopping/product decisions
- pure logistics/customer-service complaints unless they reveal pre-purchase or wishlist conversion behaviour

### 8.5 Duplicate Detection

Use two levels:

1. Exact duplicate detection using normalized-content hash.
2. Near-duplicate detection using configurable text similarity or embeddings.

Duplicates remain traceable but should not inflate pattern counts.

### 8.6 Relevance Filtering

Use a two-stage approach:

**Stage A - deterministic candidate filter**

Keyword and metadata rules cheaply identify likely relevant evidence.

**Stage B - AI relevance classifier**

The model determines whether the conversation contains useful evidence about:

- saving / shortlisting
- purchase consideration
- evaluation uncertainty
- comparison
- delay
- abandonment
- workarounds
- pre-purchase information needs

Items that are only generic praise/complaints should be marked low relevance.

---

## 9. AI Enrichment Architecture

### 9.1 Design Principle

The AI layer performs semantic interpretation, but it must not invent facts.

Every field must allow:

- known / supported value
- `unclear`
- `not_applicable`

The model should prefer `unclear` over inference when evidence is weak.

### 9.2 Structured Output

Use a strict Pydantic/JSON schema.

Example conceptual structure:

```json
{
  "wishlist_relevance": "high",
  "reason_for_saving": "comparison",
  "wishlist_intent": "genuine_purchase_consideration",
  "purchase_stage": "evaluating_alternatives",
  "behaviour_after_saving": ["revisited_item", "checked_other_apps"],
  "comparison_behaviour": "compared_similar_styles_across_platforms",
  "off_platform_research": ["youtube"],
  "workaround": "searched_creator_reviews",
  "frictions": [
    {
      "type": "emerging_or_known_category",
      "label": "uncertain_real_world_appearance",
      "severity": 3,
      "support_span": "..."
    }
  ],
  "intent_strength": 3,
  "conversion_relevance": 3,
  "proximity_to_purchase": 2,
  "evidence_confidence": 3,
  "emerging_themes": []
}
```

### 9.3 Taxonomy Design

Taxonomy is configuration, not code.

`taxonomy.yaml` should contain the current known categories from the problem statement, while preserving:

- `other`
- `emerging_theme`
- `unclear`

New themes can be reviewed and promoted into the formal taxonomy in later analysis versions.

### 9.4 Evidence-Span Requirement

For every material interpretation, the model should return a short source span that supports it.

Validation rules:

- The quoted span must exist in the masked/cleaned source text.
- If no support span exists, the classification is downgraded or rejected.
- Dashboard quotes come only from stored evidence spans, never generated prose.

### 9.5 Model Versioning

Every annotation stores:

- model provider
- model name
- prompt/schema version
- timestamp

This makes re-analysis reproducible.

---

## 10. Behavioural Segmentation Layer

Segments are not hard-coded personas.

The aggregation layer should identify combinations of recurring signals such as:

- high vs low purchase intent
- active comparison vs passive saving
- high vs low unresolved uncertainty
- frequent vs infrequent revisits
- off-platform dependence
- urgent vs low-urgency decision
- delayed vs abandoned purchase behaviour

### 10.1 Initial Method

For v1, use explainable rule-based segment candidates built from aggregate evidence.

Example candidate pattern only:

```text
High intent + active comparison + unresolved uncertainty + repeated revisit
```

This may become a segment if the evidence supports it.

### 10.2 Future Method

If data volume supports it, clustering on structured annotation fields can be added later. Any automatically generated cluster must still be translated into an explainable behavioural description before use.

---

## 11. Opportunity Synthesis Engine

The opportunity engine converts evidence patterns into research hypotheses, not product features.

### 11.1 Opportunity Format

Each opportunity should follow:

> Users with [behaviour / intent] struggle to [complete desired behaviour] because [observed friction / uncertainty], causing [delay / comparison / abandonment / workaround].

### 11.2 Opportunity Candidate Generation

Candidates are produced from combinations of:

- friction/theme
- behavioural segment signal
- purchase stage
- action after saving
- workaround
- intent strength
- source convergence

The system should require a minimum evidence threshold before promoting a pattern into a dashboard opportunity.

### 11.3 Contradictory Evidence

An opportunity can have:

- supporting evidence
- contradictory evidence
- adjacent/ambiguous evidence

Contradictions must remain visible rather than being discarded.

---

## 12. Transparent Opportunity Ranking

Mention count alone must not determine rank.

### 12.1 Item-Level Rubrics

Where supported, AI annotations use a small explainable ordinal scale, for example 0-3:

- `0` = not supported / not relevant
- `1` = weak
- `2` = moderate
- `3` = strong

Used for:

- severity
- intent strength
- conversion relevance
- proximity to purchase
- evidence confidence

### 12.2 Aggregate Opportunity Dimensions

Each opportunity is scored on:

1. **Frequency** - unique relevant evidence items, duplicate-adjusted
2. **Severity** - average/weighted severity
3. **Purchase intent** - concentration among users showing stronger purchase consideration
4. **Conversion relevance** - evidence that the issue delays/prevents a purchase decision
5. **Source convergence** - support across independent source types
6. **Segment concentration** - whether the problem is coherent within an identifiable behavioural group
7. **Evidence confidence** - directness and quality of supporting evidence

### 12.3 Initial Configurable Weighting

Initial implementation can use configurable weights such as:

```yaml
frequency: 0.20
severity: 0.15
purchase_intent: 0.20
conversion_relevance: 0.20
source_convergence: 0.10
segment_concentration: 0.05
evidence_confidence: 0.10
```

These weights are **not research findings**. They are a transparent prioritization heuristic and must be displayed/documented as such.

Weights live in `ranking.yaml`, not in code.

### 12.4 Score Output

Dashboard should show both:

- overall opportunity score
- each component score separately

This prevents the score from becoming a black box.

---

## 13. Aggregation Engine

The aggregation layer should calculate deterministic outputs from stored structured evidence.

Examples:

- raw evidence count
- retained evidence count
- source distribution
- relevance rate
- wishlist-intent distribution
- behaviour-after-saving distribution
- friction counts
- intent x friction matrix
- friction x purchase-stage matrix
- off-platform research rate among relevant evidence
- workaround frequencies
- source convergence by opportunity
- segment-signal counts
- opportunity evidence counts

All percentages must expose their denominator in the API and dashboard.

Example:

```json
{
  "label": "active comparison after saving",
  "count": 84,
  "denominator": 231,
  "percent": 36.4,
  "population": "relevant evidence where post-save behaviour is identifiable"
}
```

This prevents ambiguous statistics.

---

## 14. Backend API Design

Initial API surface:

### Health / metadata

- `GET /api/health`
- `GET /api/meta`

### Dashboard

- `GET /api/dashboard/summary`
- `GET /api/dashboard/patterns`
- `GET /api/dashboard/segments`

### Evidence

- `GET /api/evidence`
- `GET /api/evidence/{id}`

Supported filters may include:

- source
- date
- friction/theme
- intent
- stage
- segment signal
- severity
- confidence

### Opportunities

- `GET /api/opportunities`
- `GET /api/opportunities/{id}`
- `GET /api/opportunities/{id}/evidence`

### Pipeline

- `POST /api/pipeline/sample-run`
- `GET /api/pipeline/runs/{id}`

Full pipeline execution should use an authenticated internal endpoint or scheduled worker, not an unrestricted public API.

### Human review

- `POST /api/review/{annotation_id}/flag`
- `POST /api/review/{annotation_id}/override`

Human-review writes should be protected from general evaluator access.

---

## 15. Real Evaluator Sample Run

The public dashboard should include a safe action such as:

> **Run Fresh Sample**

This is a real pipeline execution, not a visual simulation.

### Sample-run behaviour

1. Create a pipeline job.
2. Pull a capped number of fresh/recent items from one or more reliable sources.
3. Deduplicate and preprocess.
4. Run relevance filtering.
5. AI-analyze the retained sample.
6. Persist results under the sample run.
7. Recompute or display sample-specific findings.
8. Stream/poll genuine job status to the frontend.

### Safety limits

- strict item cap
- request cooldown
- rate-limit protection
- LLM token/cost cap
- timeout handling
- only public, permitted sources

The full dashboard should continue to use the larger preprocessed corpus so evaluator experience does not depend on a live scraper succeeding at that exact moment.

---

## 16. Dashboard Information Architecture

The dashboard should prioritize product insight over technical novelty.

### 16.1 Overview

Show:

- total raw evidence
- retained relevant evidence
- source count/distribution
- most recent pipeline run
- analysis version
- high-level behavioural findings

### 16.2 Behaviour Explorer

Charts/tables for:

- reasons for saving where identifiable
- purchase-intent patterns
- post-save behaviours
- decision stages
- major frictions/uncertainties
- off-platform research
- workarounds

Every percentage should expose count + denominator.

### 16.3 Segment Explorer

Show emerging behavioural segment signals and how their evidence differs.

The screen should avoid pretending that segments are statistically representative of Myntra's entire customer base.

### 16.4 Opportunity Board

For each opportunity:

- statement
- overall score
- component scores
- evidence count
- source count
- strongest segment signal
- representative evidence
- contradictory evidence count
- confidence

### 16.5 Evidence Drill-Down

Clicking a finding/opportunity opens the underlying evidence list.

Display:

- masked quote
- source type
- date
- behavioural annotations
- confidence
- why it was linked to the opportunity

### 16.6 Pipeline Page

Show real stages:

```text
Collect -> Clean -> Deduplicate -> Relevance -> Analyze -> Aggregate -> Rank
```

For each run show actual:

- status
- counts
- duration
- errors/warnings

---

## 17. Human-in-the-Loop Architecture

The engine must support auditability even if most evaluator interactions are read-only.

### Workflow

1. Reviewer opens an evidence item.
2. Sees masked source evidence and AI annotation.
3. Accepts, flags, or overrides a field.
4. Override is stored separately.
5. Aggregation prefers reviewed value when present.
6. Original AI output remains preserved.

### Review Sampling

During development, manually review:

- a random sample of annotations
- high-impact opportunity evidence
- low-confidence items
- contradictory items
- cases where AI detects emerging themes

---

## 18. Validation and Hallucination Controls

### 18.1 Schema Validation

Every AI response must pass Pydantic/JSON schema validation.

Invalid responses are retried with a bounded retry policy and then marked failed rather than silently accepted.

### 18.2 Evidence-Span Validation

Supporting quote/spans must be found in the cleaned/masked source text.

Generated quotes are rejected.

### 18.3 Confidence Discipline

If evidence does not explicitly support a field:

- output `unclear`
- lower evidence confidence
- do not force classification

### 18.4 Deterministic Arithmetic

LLMs never calculate final counts, percentages, or opportunity ranking arithmetic.

The backend calculates these from stored structured fields.

### 18.5 Human Validation Set

Create a small manually labeled validation set during implementation.

Use it to test:

- relevance precision
- intent extraction
- friction/theme accuracy
- workaround extraction
- support-span correctness
- false-positive rate

The goal is not academic model benchmarking; it is to know where the engine can and cannot be trusted.

---

## 19. Pipeline Execution Model

### 19.1 Full Pipeline

```text
Scheduled/manual trigger
        |
        v
Create collection_run
        |
        v
Run enabled connectors
        |
        v
Persist raw evidence
        |
        v
Normalize + mask PII
        |
        v
Deduplicate
        |
        v
Relevance filter
        |
        v
AI enrichment in batches
        |
        v
Validate + persist annotations
        |
        v
Aggregate patterns
        |
        v
Generate opportunity candidates
        |
        v
Calculate transparent scores
        |
        v
Publish dashboard snapshot
```

### 19.2 Incremental Processing

Previously analyzed source items should not be re-analyzed unless:

- prompt/schema version changes
- taxonomy version changes
- human reviewer requests re-analysis
- evidence text changes

This reduces cost and makes pipeline runs faster.

---

## 20. Error Handling and Resilience

### Source failures

If one source fails:

- record the error
- continue with other enabled sources
- show the degraded run in pipeline metadata

### AI failures

- bounded retry with backoff
- preserve failure status
- never generate placeholder annotations

### Rate limits

- connector-specific delay/backoff
- capped sample runs
- source-level quotas

### Database failures

- transaction boundaries around batch writes
- idempotent source-item keys

### Partial pipeline runs

A run can complete with warnings if enough sources succeed. Dashboard must show the warning rather than imply complete coverage.

---

## 21. Security, Privacy, and Compliance

### Secrets

All API keys and credentials must live in deployment environment variables.

Never commit:

- `.env`
- API keys
- service-role tokens
- database passwords

### Database access

- Public frontend uses backend APIs, not Supabase service-role credentials.
- Admin/human-review write endpoints require authentication or secret protection.
- Evaluator dashboard is read-only except the controlled sample-run action.

### PII

- raw evidence is server-side only
- masked evidence is used in public UI
- unnecessary author identifiers are not stored/displayed where avoidable

### Source compliance

Only collect public content through technically and legally permitted mechanisms.

Do not bypass:

- logins
- CAPTCHAs
- anti-bot systems
- paywalls
- access restrictions

If a source cannot be used reliably within these limits, remove it rather than engineer around the restriction.

---

## 22. Deployment Architecture

```text
                         Internet
                            |
                            v
                 +--------------------+
                 | Vercel             |
                 | Next.js Dashboard  |
                 +---------+----------+
                           |
                           | HTTPS API
                           v
                 +--------------------+
                 | Railway            |
                 | FastAPI Backend    |
                 | Pipeline Worker    |
                 +----+----------+----+
                      |          |
                      |          +----------------+
                      |                           |
                      v                           v
             +----------------+           +---------------+
             | Supabase       |           | AI Provider   |
             | PostgreSQL     |           | Gemini/Groq   |
             +----------------+           +---------------+
                      ^
                      |
              GitHub Actions
              scheduled trigger
```

### Environments

At minimum:

- local development
- production

If time permits:

- staging/preview via Vercel preview deployments

---

## 23. Observability

Every pipeline run should capture:

- source start/end
- source item counts
- dedup counts
- relevance counts
- AI success/failure counts
- token/request usage where available
- duration per stage
- final opportunity count
- warnings/errors

Use structured logs.

The dashboard only needs a simple run-status view; engineering logs can remain backend-only.

---

## 24. Performance and Cost Controls

The project does not need hyperscale infrastructure.

Controls:

- analyze only new/relevant items
- batch model requests where supported
- cap text length while preserving relevant context
- cache completed annotations by text hash + analysis version
- use deterministic pre-filtering before AI
- cap evaluator sample runs
- rate-limit expensive endpoints

The goal is repeatability and credibility, not maximum throughput.

---

## 25. Testing Architecture

### Unit tests

Test:

- connector output normalization
- text cleaning
- PII masking
- duplicate detection
- ranking arithmetic
- denominator calculations

### Integration tests

Test:

- connector -> database
- evidence -> preprocessing -> annotation
- annotation -> aggregation
- opportunity -> evidence drill-down
- API -> dashboard payload

### AI contract tests

Use fixed test evidence to verify:

- JSON schema compliance
- `unclear` behaviour
- supporting-span validity
- no fabricated quotes
- taxonomy + emerging theme behaviour

### End-to-end smoke test

A small run must successfully perform:

```text
public source -> raw evidence -> clean evidence -> AI annotation
-> aggregate -> opportunity -> dashboard
```

### Deployment smoke test

From an incognito/logged-out browser:

- dashboard loads
- charts/data load
- evidence drill-down works
- opportunity evidence works
- sample run can be started within limits
- sample run shows real state changes
- no secrets are exposed in client/network payloads

---

## 26. Research Integrity Safeguards

The architecture must actively prevent the engine from becoming a confirmation machine.

### Required safeguards

1. Taxonomy contains `other`, `emerging`, and `unclear` states.
2. Prompt instructs the model not to infer unsupported causes.
3. Opportunity synthesis requires evidence, not theme popularity alone.
4. Contradictory evidence is retained.
5. Opportunity weights are visible/configurable.
6. Statistics expose denominators.
7. Public-review patterns are described as hypotheses, not population-level truths.
8. Final target segment is chosen after analysis, not embedded in source filters.
9. The engine outputs opportunity statements, never final feature recommendations.
10. Primary interviews remain a required next validation stage.

---

## 27. What the Engine Must NOT Do

The architecture should prevent or discourage these behaviours:

- Hard-code "fit", "price", or any other theme as the winner.
- Treat all wishlist additions as purchase intent.
- Use sentiment as the main opportunity-ranking mechanism.
- Count duplicates as independent evidence.
- Let the LLM invent representative quotes.
- Rank solely by mention count.
- Display percentages without denominators.
- Claim a public-review sample represents all Myntra users.
- Generate the final MVP feature from the engine automatically.
- Simulate a pipeline run in the evaluator UI.

---

## 28. Architecture Decisions That Differ From the Previous Spotify Engine

The Myntra engine intentionally improves on the previous approach in several ways:

1. **Behaviour-first schema:** analysis captures intent, post-save action, workaround, decision stage, and conversion relevance rather than mainly themes/sentiment.
2. **Evidence-linked classifications:** important annotations require supporting source spans.
3. **Transparent opportunity ranking:** frequency is only one input.
4. **Denominator-aware metrics:** every percentage has a defined population.
5. **Contradiction preservation:** evidence can support or challenge an opportunity.
6. **Human override layer:** AI classifications can be reviewed without destroying original output.
7. **Configurable taxonomy and ranking:** research outcomes are not embedded in code.
8. **Real evaluator sample run:** the dashboard can execute a small real pipeline job rather than simulate progress.
9. **Opportunity output, not feature output:** the engine hands off hypotheses to interviews rather than deciding the solution.

---

## 29. Definition of Done for Architecture

This architecture is complete enough to move into implementation planning when:

- system boundaries are clear
- source connector pattern is defined
- storage model preserves raw and interpreted evidence separately
- preprocessing responsibilities are clear
- AI responsibilities and safeguards are defined
- behavioural schema is implementable
- opportunity scoring is transparent
- human review is supported
- API/dashboard boundaries are defined
- deployment path is feasible
- sample-run behaviour is real and bounded
- privacy/security requirements are explicit
- testing strategy covers the end-to-end evidence chain
- nothing in the architecture predetermines the final research finding or MVP

The next document should be:

> **`implementation plan.md`** - a phased build sequence with deliverables, test criteria, and deployment checkpoints for each phase.
