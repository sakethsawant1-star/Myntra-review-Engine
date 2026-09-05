# Antigravity Implementation Brief: Refine the Existing Myntra Review Engine In Place

## 0. Read This First

This document is the single implementation and interface-design specification for refining the Review/Discovery Engine that already exists in this repository.

**This is not a request to rebuild the graduation project or start a new repository.**

Continue from the current codebase. Preserve working components. Make targeted changes only where the existing implementation does not satisfy the project problem statement, research-integrity requirements, evaluator experience, or the planned deployment architecture.

The intended production setup is:

- **Frontend:** the existing static HTML/CSS/JavaScript frontend, refined and deployed on Vercel
- **Backend API:** the existing FastAPI application, refined and deployed on Railway
- **Background processing:** the existing Python pipeline, run by a Railway worker service or another Railway process using the same repository
- **Database:** the existing Supabase PostgreSQL database
- **AI analysis:** the existing Gemini provider abstraction, made configurable and more complete

Do not migrate the frontend to React, Next.js, or another framework merely because the old README mentions Next.js. The actual project currently uses vanilla HTML, CSS, and JavaScript. Keep that approach unless an unavoidable technical limitation is demonstrated. The goal is to improve the existing engine, not to create avoidable migration work.

Before changing code, read these files in this order:

1. `original fellowship brief.md`
2. `Docs/problem statement.md`
3. `Docs/architecture.md`
4. `Docs/implementation plan.md`
5. `Docs/AG_CONTEXT.md`
6. `decisions.md`
7. `README.md`
8. All existing backend, frontend, database, configuration, and test files

Then inspect the actual repository state. Do not assume the documentation is fully aligned with the code.

---

# 1. The Exact Product Goal

The graduation-project business goal is to increase:

> **The percentage of users who purchase at least one item from their Myntra wishlist within 30 days of adding an item.**

The engine does not have access to Myntra's private behavioral or conversion data and therefore must not claim to calculate Myntra's actual conversion rate.

Its role is to analyze public conversations and convert them into transparent, evidence-backed **opportunity hypotheses** that deserve deeper primary research.

The engine must help answer all of the following questions:

1. Why do users save fashion products to wishlists?
2. When does a wishlist represent genuine purchase intent versus passive bookmarking?
3. What prevents users with purchase intent from completing a purchase?
4. What uncertainty remains after a user has already identified an item they like?
5. What causes users to postpone the decision rather than buy immediately?
6. What happens after wishlisting and before purchase or abandonment?
7. How do users compare multiple shortlisted products?
8. What information do users seek outside Myntra before deciding?
9. What workarounds do users use when Myntra does not resolve their uncertainty?
10. How do these behaviors vary across identifiable behavioral segments?
11. Which recurring unmet needs appear most likely to influence 30-day wishlist-to-purchase conversion?

The interface must make it obvious where the answer to each question comes from, how much evidence supports it, what denominator is used, how confident the system is, and where the evidence is weak.

The engine's valid final output is:

> **Prioritized opportunity hypotheses for interviews.**

The engine must not automatically decide the final customer-facing MVP or describe an AI-generated hypothesis as a proven root cause.

---

# 2. Current Repository: What Must Be Preserved

The existing repository already contains useful work. Preserve and refine the following instead of replacing them:

- `backend/app/connectors/`
  - Google Play connector
  - Apple App Store connector
  - Reddit connector
  - YouTube connector
  - URL importer
  - common `RawEvidenceItem` contract
- `backend/app/pipeline/preprocessor.py`
  - normalization
  - PII masking
  - language handling
  - deterministic noise and candidate filtering
- `backend/app/pipeline/pipeline.py`
  - collection
  - preprocessing
  - Gemini enrichment
  - persistence
  - run statistics
- `backend/app/ai/`
  - provider abstraction
  - strict Pydantic output model
  - research-neutral prompt foundations
- `backend/app/scoring/`
  - aggregations
  - rule-based segment generation
  - opportunity generation
  - transparent ranking configuration
- `database/migrations/0001_initial_schema.sql`
  - raw evidence
  - processed evidence
  - annotations
  - human reviews
  - opportunities
  - opportunity evidence
- `frontend/`
  - current single-page dashboard
  - dark Myntra-inspired visual system
  - tabs and basic rendering logic
- current automated tests

Do not remove a working component just because a cleaner implementation could be written from scratch. Extend or refactor it in place, maintain compatibility where practical, and document every material change.

---

# 3. Current Gaps That Must Be Fixed

The following gaps were identified from a static review of the current ZIP. Treat them as required refinement work, not optional polish.

## 3.1 Frontend integrity gaps

### Hard-coded analytics

`frontend/app.js` currently contains a large `MOCK_DATA` object with fixed numbers and predetermined findings. Examples include fixed corpus counts, fit uncertainty as the leading issue, cross-platform percentages, and fixed opportunity scores.

These values must not appear as real findings.

### Estimated raw evidence count

The current `renderOverview()` estimates raw evidence using:

```javascript
summary.total_annotations * 3.4
```

This must be removed. Raw counts must come from actual database records and actual run-stage outputs.

### Hard-coded API base URL

The frontend currently uses:

```javascript
const API_BASE = 'http://localhost:8000/api';
```

Replace this with a build-time or runtime configuration suitable for Vercel.

### Misleading fallback behavior

When the backend is unavailable, the interface silently falls back to mock findings. This can make a disconnected frontend look like a live research engine.

Replace it with one of these explicit states:

- `Live data unavailable`
- `Prepared demo dataset`
- `Illustrative interface preview`

A demo dataset may remain for development, but it must be enabled deliberately, not automatically, and the interface must show a persistent `DEMO DATA` banner.

### Evidence is always mock evidence

The current frontend fetches summary, segments, and opportunities, but evidence is always rendered from `MOCK_DATA.evidence`. Replace this with real evidence endpoints.

### Pipeline view is simulated

The pipeline stepper and logs are hard-coded as completed. The button only displays an alert after calling a trigger endpoint. Replace this with real run creation, a returned `run_id`, status polling, stage counts, durations, warnings, and errors.

### Predetermined discovery story

The current HTML says fit uncertainty is the top issue before live data has established that finding. Remove all predetermined findings from HTML, JavaScript, seed presentation, and interface copy.

## 3.2 Backend and API gaps

### Pipeline trigger is incomplete

The current route:

- starts a FastAPI `BackgroundTask`
- triggers only `GooglePlayConnector`
- does not reliably use the submitted limit
- returns no `run_id`
- provides no status endpoint
- is not resilient to Railway restarts
- cannot show genuine per-stage progress

Replace it with a database-backed run queue and status model while reusing the existing pipeline.

### Missing API surfaces

The existing API does not fully expose:

- metadata and methodology
- actual pipeline runs and run stages
- evidence list and evidence detail
- opportunity detail and linked evidence
- question-coverage results
- human-review state
- prepared corpus versus fresh sample scope
- survey validation snapshot

Add only the routes required to support the refined interface.

### Incomplete persistence

The AI output model contains many behavioral fields, but the pipeline currently saves only a subset and stores several values inside `analysis_notes` as a string.

Stop encoding structured data inside `analysis_notes`.

Persist the structured fields in their intended columns, including:

- reason for saving
- wishlist intent
- purchase stage
- behavior after saving
- revisit behavior
- comparison behavior
- off-platform research
- workaround
- purchase trigger
- abandonment signal
- frictions and support spans
- emerging themes
- intent strength
- severity
- conversion relevance
- proximity to purchase
- segment signals
- evidence confidence
- supporting spans

### Processed evidence is not stored for every item

The current pipeline stores `processed_evidence` only for AI candidates. This makes a complete retention funnel impossible to audit.

Every new raw item must receive a processed-evidence record showing what happened to it:

- duplicate
- noise
- unsupported language
- candidate rejected
- AI candidate
- AI retained
- AI not relevant
- AI failed

### Cleaned and masked text are conflated

The preprocessor returns masked text under the `cleaned_text` key. Store these separately:

- `cleaned_text`: normalized source text
- `masked_text`: PII-masked text used for public display and AI processing

Never expose unmasked raw text publicly if it may contain PII.

## 3.3 AI schema and taxonomy gaps

The current schema is narrower than the problem statement. It omits or compresses relevant areas such as:

- styling or coordination uncertainty
- product-quality uncertainty as distinct from generic trust
- review or trust uncertainty
- occasion suitability
- social validation
- comparison difficulty
- availability or stock concern
- delivery or timing concern
- return or exchange concern
- choice overload
- forgetting or low salience
- open emerging themes

Refine the schema without forcing every evidence item into a category.

Important rules:

- `unclear` and `not_applicable` must remain valid outputs.
- Multiple post-save behaviors may coexist; store them as a list.
- Multiple reasons for saving may coexist; either use a list or a primary reason plus secondary reasons.
- Multiple frictions may coexist.
- Exact supporting spans must be present for important claims.
- A deterministic validator must confirm that an exact quote appears inside the masked source text.
- Unsupported fields must be cleared, downgraded, or flagged for review.
- AI may discover an `other` or `emerging_theme`; the taxonomy cannot decide the winner in advance.

Make the Gemini model configurable through an environment variable such as `GEMINI_MODEL`. Do not hard-code a model version throughout the codebase. Preserve temperature 0 or similarly deterministic structured extraction.

## 3.4 Aggregation gaps

The current aggregator fetches only a subset of annotation columns and derives intent strength by searching text inside `analysis_notes`. Replace this with direct structured queries.

The aggregator must calculate actual counts and denominator-aware metrics for:

- source distribution
- retention funnel
- reason for saving
- wishlist intent
- purchase stage
- post-save behavior
- revisit behavior
- comparison behavior
- off-platform research
- workarounds
- purchase triggers
- abandonment signals
- frictions
- friction severity
- intent by friction
- proximity to purchase
- evidence confidence
- unclear or unclassified rate
- human-reviewed rate
- research-question coverage

## 3.5 Segment gaps

The current segment system hard-codes four candidate segments. Keep rule-based segmentation, but improve it so that:

- segment definitions are transparent
- segment rules are configurable
- segments may overlap, and overlap is disclosed
- every segment has a clear denominator
- segment evidence can be inspected
- segment names are descriptive but not judgmental
- segment promotion requires a configurable minimum evidence threshold
- current survey behaviors may inform interview recruitment, but survey labels must not be injected into public-review evidence

Do not automatically select one segment as the final target.

## 3.6 Opportunity-ranking gaps

The problem statement requires seven ranking dimensions. The current `ranking.yaml` and ranker use six and omit segment concentration.

Add and expose all seven:

1. Frequency
2. Severity
3. Purchase-intent strength
4. Conversion relevance
5. Source convergence
6. Segment concentration
7. Evidence confidence

Fix these current issues:

- Frequency must not be only relative to the highest-ranked opportunity.
- Severity must come from actual annotation severity, not a hard-coded friction dictionary alone.
- Purchase intent must come from actual `intent_strength` and purchase stage.
- Conversion relevance must come from annotations and transparent rules, not only from the segment name.
- Source convergence must account for the actual number of usable enabled sources.
- Evidence confidence must be calculated on the opportunity's linked evidence, not the entire corpus.
- Segment concentration must be calculated and displayed.
- Opportunity evidence must be persisted with `support`, `contradict`, or `adjacent` relationship types.
- Opportunity wording must not introduce unsupported explanations, such as asserting that Myntra lacks trust signals when the evidence only shows off-platform research.

## 3.7 Human-review gaps

The database has a `human_reviews` table, but the workflow is not exposed or used by aggregation.

Add an admin-protected review workflow that allows an authorized researcher to:

- inspect masked evidence
- inspect AI fields and exact support spans
- accept the annotation
- flag it
- override specific fields
- add a note
- preserve the original AI output

When a reviewed override exists, aggregations should use the effective reviewed value while retaining the original AI result for audit.

Do not expose admin controls publicly.

## 3.8 Deployment and security gaps

- Remove `.env` from shared ZIP files and version control.
- Ensure `.gitignore` excludes `.env`, `venv`, caches, generated exports, and local data.
- Rotate credentials if the `.env` archive was shared beyond the trusted project environment.
- Restrict CORS to the Vercel production URL and configured local development origins.
- Never expose the Supabase service-role key in frontend code.
- Protect pipeline trigger abuse with caps, cooldowns, and rate limits.
- Protect human-review writes with an admin token or authentication layer.
- Update README to reflect the actual vanilla frontend and Railway deployment.

---

# 4. Scope of This Refinement

## Required

Refine the existing engine so that it can:

1. Run a small genuine fresh sample safely.
2. Display actual per-stage progress.
3. Display a larger prepared corpus separately from the fresh sample.
4. Show real denominator-aware findings.
5. Answer the 11 discovery questions.
6. Generate transparent behavioral segments.
7. rank multiple opportunity hypotheses across seven dimensions.
8. link every major finding to evidence.
9. show supporting and contradictory evidence.
10. show where the evidence is weak or unclear.
11. keep AI review findings, survey signals, and interviews as separate evidence layers.
12. deploy the frontend to Vercel and backend/worker to Railway.

## Not required

Do not use this task to:

- rebuild the final customer-facing Myntra MVP
- choose a final solution before interviews
- migrate the frontend framework
- create a new repository
- rewrite all connectors
- replace Supabase
- add complex authentication for public read-only pages
- create a fake live pipeline animation
- claim public-review findings represent all Myntra users
- add monetary-incentive recommendations

---

# 5. Target Architecture: Delta From the Existing System

Preserve the current components and connect them as follows:

```text
Vercel Static Frontend
        |
        | HTTPS read requests + controlled sample-run request
        v
Railway FastAPI Service
        |
        | creates DB-backed run jobs and serves analysis endpoints
        v
Supabase PostgreSQL
        ^
        |
Railway Worker Service
        |
        | reuses existing connectors -> preprocessor -> Gemini -> aggregator -> ranker
        v
Public Sources + Gemini API
```

Use two Railway services from the same repository when practical:

### Railway API service

Suggested start command:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Responsibilities:

- public read endpoints
- health and metadata
- sample-run creation
- run status
- evidence and opportunity queries
- protected reviewer writes

### Railway worker service

Suggested start command:

```bash
python -m backend.app.worker
```

Responsibilities:

- poll queued runs
- execute the existing pipeline
- update each stage in Supabase
- calculate aggregations and opportunities after a run
- recover safely after restarts

If the worker is temporarily kept inside one Railway service, the database-backed run and status model is still mandatory. Do not rely only on in-memory FastAPI `BackgroundTasks` for production.

---

# 6. Database Refinement

Create a new additive migration such as:

```text
database/migrations/0002_engine_refinement.sql
```

Do not destroy existing data. Use additive columns, new tables, indexes, views, and safe backfills.

## 6.1 Refine `collection_runs`

Add fields where missing:

- `dataset_scope`: `fresh_sample`, `prepared_corpus`, `manual_import`, or `demo`
- `requested_item_cap`
- `requested_sources` JSONB
- `enabled_sources` JSONB
- `successful_sources` JSONB
- `failed_sources` JSONB
- `current_stage`
- `progress_percent`
- `items_unique`
- `items_processed`
- `items_relevant`
- `items_ai_attempted`
- `items_ai_succeeded`
- `items_ai_failed`
- `items_human_reviewed`
- `model_provider`
- `model_name`
- `analysis_version`
- `processing_version`
- `ranking_version`
- `warnings` JSONB
- `requested_at`
- `heartbeat_at`
- `error_summary`

Keep the existing fields for compatibility.

## 6.2 Add `collection_run_stages`

Suggested columns:

- `id`
- `run_id`
- `sequence_number`
- `stage_key`
- `stage_label`
- `status`: `pending`, `running`, `completed`, `completed_with_warnings`, `failed`, `skipped`
- `input_count`
- `output_count`
- `rejected_count`
- `started_at`
- `completed_at`
- `duration_ms`
- `warnings` JSONB
- `error_message`
- `metadata` JSONB

Add a unique constraint on `(run_id, stage_key)`.

Use these visible stage keys:

1. `collect`
2. `normalize`
3. `mask_pii`
4. `deduplicate`
5. `relevance_filter`
6. `ai_extract`
7. `validate_evidence`
8. `aggregate`
9. `rank_opportunities`

The existing pipeline can continue to perform some stages inside one function, but it must emit separate stored stage updates for evaluator traceability.

## 6.3 Refine `processed_evidence`

Ensure these fields are populated:

- `cleaned_text`
- `masked_text`
- `language`
- `is_duplicate`
- `duplicate_of`
- `spam_score`
- `relevance_status`
- `relevance_score`
- `processing_version`
- `processed_at`
- `canonical_hash`

Store a row for every collected item, not only items sent to Gemini.

## 6.4 Refine `evidence_annotations`

Ensure all structured AI fields have direct columns or JSONB storage. Add:

- `reason_for_saving` JSONB or primary/secondary columns
- `behaviour_after_saving` JSONB
- `revisit_behaviour`
- `comparison_behaviour`
- `off_platform_research` JSONB
- `workaround`
- `purchase_trigger`
- `abandonment_signal`
- `frictions` JSONB
- `emerging_themes` JSONB
- `intent_strength`
- `severity`
- `conversion_relevance`
- `proximity_to_purchase`
- `segment_signals` JSONB
- `evidence_confidence`
- `supporting_spans` JSONB
- `support_span_validation` JSONB
- `annotation_status`
- `analysis_version`
- `created_at`

Stop using `analysis_notes` as a substitute for these fields. Keep `analysis_notes` only for genuine analyst/model notes.

## 6.5 Refine opportunities

Ensure the opportunities table stores:

- title
- neutral opportunity statement
- behavioral segment
- dominant friction or unmet need
- affected journey stage
- seven component scores
- overall score
- evidence count
- contradiction count
- adjacent evidence count
- source count
- strongest source share
- confidence label
- status: `emerging`, `shortlisted_for_interviews`, `confirmed`, `refined`, `challenged`, `rejected`
- score and taxonomy versions
- generated timestamp

Use `opportunity_evidence.relationship_type` with:

- `support`
- `contradict`
- `adjacent`

## 6.6 Optional survey snapshot storage

Do not merge survey rows into the public-review tables.

Add either:

- `survey_snapshots` and `survey_aggregates` tables, or
- a generated, versioned JSON snapshot loaded by the API

Store only aggregate survey results for the public dashboard. Never expose names, phone numbers, email addresses, or interview contact details.

---

# 7. AI Analysis Contract

Refine `backend/app/ai/schema.py` and `prompts.py` in place.

A useful target contract is shown conceptually below. Adapt it to Pydantic rather than copying blindly.

```text
wishlist_relevance
reason_for_saving[]
wishlist_intent
intent_strength
purchase_stage
proximity_to_purchase
behaviour_after_saving[]
revisit_behaviour
comparison_behaviour
off_platform_research[]
information_sought[]
workaround[]
purchase_trigger[]
abandonment_signal[]
frictions[]
emerging_themes[]
conversion_relevance
evidence_confidence
supporting_spans[]
contradictory_signal
analysis_notes
```

## 7.1 Initial taxonomy

The initial taxonomy may include these values, but the model must be allowed to return `other`, `emerging_theme`, `unclear`, and `not_applicable`.

### Reasons for saving

- genuine purchase consideration
- compare alternatives
- buy later
- price monitoring
- future event or occasion
- inspiration or bookmarking
- availability monitoring
- unclear
- other

### Wishlist intent

- high purchase intent
- active comparison
- delayed purchase intent
- passive bookmarking
- price monitoring
- unclear
- not applicable

### Purchase stage

- browsing
- shortlisted
- evaluating alternatives
- resolving uncertainty
- ready to buy
- delayed
- abandoned
- purchased
- unclear

### Post-save behaviors

- revisited item
- compared within Myntra
- compared across platforms
- checked reviews
- searched Google
- searched YouTube
- checked social content
- asked another person
- added to bag
- waited
- forgot
- bought elsewhere
- bought another item
- no action stated
- unclear
- other

### Frictions and uncertainties

- fit uncertainty
- size uncertainty
- styling or coordination uncertainty
- product-quality uncertainty
- review or trust uncertainty
- product-information gap
- occasion suitability
- social validation
- comparison difficulty
- availability or stock concern
- delivery or timing concern
- price-related behavior
- return or exchange concern
- choice overload
- forgetting or low salience
- platform usability issue
- other emerging friction
- unclear

## 7.2 Prompt rules

The prompt must explicitly state:

- Do not assume every wishlist addition is purchase intent.
- Do not infer a wishlist when the source only contains a generic app complaint.
- Do not invent a delay, blocker, comparison, workaround, or purchase trigger.
- Use `unclear` when evidence is weak.
- Extract exact substrings as support.
- Do not generate a product feature or solution.
- Do not guess demographics.
- Separate stated facts from model inference.
- Do not let the survey findings bias public-review classification.
- Do not promote price, fit, reviews, or any other category as the expected answer.

## 7.3 Evidence-span validation

After Gemini returns an annotation:

1. normalize both the masked source text and support span conservatively
2. verify that each claimed quote exists in the masked source text
3. mark the field valid or invalid
4. downgrade confidence or clear unsupported fields
5. persist validation results
6. flag high-impact invalid annotations for human review

Representative quotes shown publicly must always come from stored source spans. Never display an AI-written paraphrase as a user quote.

---

# 8. Pipeline Refinement

Refactor the existing `Pipeline` class rather than replacing it.

## 8.1 Run creation

Implement:

```http
POST /api/pipeline/runs
```

Request example:

```json
{
  "scope": "fresh_sample",
  "sources": ["google_play", "reddit"],
  "item_cap": 40
}
```

Response example:

```json
{
  "run_id": "uuid",
  "status": "queued",
  "scope": "fresh_sample",
  "item_cap": 40,
  "poll_url": "/api/pipeline/runs/uuid"
}
```

The request must return quickly. The worker performs the long-running job.

## 8.2 Safe evaluator sample

The public `Run Fresh Sample` action must have:

- a strict total item cap, suggested default 30 to 50
- a per-source cap
- a maximum AI-analysis cap
- a cooldown per IP or shared public cooldown
- only explicitly enabled, reliable sources
- timeout handling
- partial-success behavior
- visible source warnings
- no unrestricted full-corpus trigger

The larger prepared corpus remains the default dashboard dataset.

## 8.3 Connector selection

Build connector instances from configuration and available credentials.

Do not show a source as active unless:

- it is enabled in configuration
- required credentials are present
- the latest relevant run attempted it
- the status is stored

Pass the requested limit into connector collection. Do not instantiate a connector and silently ignore the request cap.

## 8.4 Store complete funnel state

For every item:

```text
Raw collected
-> Normalized
-> PII masked
-> Duplicate or unique
-> Noise/candidate status
-> AI relevance
-> Structured annotation
-> Evidence-span validation
-> Aggregation
-> Opportunity linkage
```

Persist the outcome even when an item drops out.

## 8.5 Run status

Implement:

```http
GET /api/pipeline/runs/{run_id}
GET /api/pipeline/runs/latest?scope=prepared_corpus
```

Return:

- overall status
- current stage
- progress percentage
- stage list
- actual input/output counts
- source results
- durations
- warnings
- errors
- versions
- start and completion time

The frontend must poll this endpoint until the run reaches a terminal state.

## 8.6 Prepared corpus versus fresh sample

Every dashboard endpoint must support a data scope:

- `prepared_corpus`: the stable larger dataset used for main findings
- `fresh_sample`: one evaluator-triggered run
- optional explicit `run_id`
- `demo`: only when intentionally enabled and clearly labelled

Never mix the denominator of a fresh sample with prepared-corpus findings.

---

# 9. Required Metrics and Exact Definitions

All metrics must show a count, a denominator, and a definition. When a field permits multiple values, state that category percentages can sum above 100%.

## 9.1 Pipeline and data-quality metrics

### Raw conversations collected

```text
Count of raw_evidence rows linked to the selected run or corpus snapshot.
```

### Unique conversations

```text
Raw conversations not marked duplicate after normalized/cross-source deduplication.
```

### Duplicate rate

```text
Duplicate items / Raw conversations collected
```

### Noise rejection rate

```text
Items marked noise / Unique conversations
```

### Decision-relevance yield

```text
Evidence retained as wishlist or purchase-decision relevant / Unique non-noise conversations
```

### AI annotation success rate

```text
Valid stored annotations / Items sent to AI
```

### Support-span validation rate

```text
Important annotation claims with verified exact support spans / Important annotation claims checked
```

### Human-review coverage

```text
Annotations reviewed by a human / Retained annotations
```

### Active sources

```text
Distinct sources that produced at least one retained item in the selected scope
```

Do not hard-code this number.

## 9.2 Behavioral research metrics

### Reason-for-saving incidence

```text
Relevant evidence items containing a reason-for-saving category / Relevant evidence items where a reason for saving was identifiable
```

Also show `identifiable coverage`:

```text
Evidence items with identifiable reason / All retained relevant evidence
```

### Wishlist-intent distribution

Show count and share for each intent category. Include `unclear` rather than hiding it.

### High-intent blocked rate

```text
High-intent evidence items containing at least one medium/high blocking friction / High-intent evidence items
```

### Post-save behavior incidence

```text
Evidence items containing the behavior / Evidence items where post-save behavior was assessable
```

### Off-platform research rate

```text
Evidence items showing any off-platform research / Evidence items where post-save behavior was assessable
```

Also break down destinations such as other shopping platforms, Google, YouTube, social content, communities, or offline stores when supported.

### Comparison leakage rate

```text
Evidence items showing cross-platform product comparison or purchase elsewhere / Evidence items showing active comparison
```

Use careful language: this is evidence incidence inside the corpus, not Myntra's actual population leakage rate.

### Delay signal rate

```text
Evidence items containing delay behavior / Evidence items with genuine, active, or delayed purchase intent
```

### Workaround incidence

```text
Evidence items containing a workaround / Evidence items containing an unresolved friction
```

### Purchase-trigger incidence

```text
Evidence items containing a stated trigger / Evidence items describing a wishlist-to-purchase conversion
```

### Unclear rate

```text
Annotations with unclear key behavioral fields / Retained annotations
```

High unclear rates should reduce confidence, not be hidden.

## 9.3 Research-question coverage

Create a coverage record for each of the 11 questions.

Each record must contain:

- question number
- question text
- fields used
- evidence items capable of answering it
- retained-corpus denominator
- coverage percentage
- top signal, if any
- confidence
- evidence link
- limitation

Coverage is not the same as certainty. A question can have high coverage and conflicting evidence.

## 9.4 Seven-factor opportunity score

Use configurable weights that sum to 1.0. A recommended default is:

```yaml
weights:
  frequency: 0.15
  severity: 0.15
  purchase_intent: 0.20
  conversion_relevance: 0.20
  source_convergence: 0.10
  segment_concentration: 0.10
  evidence_confidence: 0.10
```

The weights intentionally prevent mention volume from dominating.

### Frequency

Use opportunity evidence incidence within the relevant eligible corpus, not only evidence count relative to the top opportunity.

```text
supporting opportunity evidence / eligible retained evidence
```

Normalize using documented configurable thresholds.

### Severity

Use the average or weighted distribution of annotation-level friction severity for supporting evidence.

### Purchase intent

Use actual intent strength and proximity to purchase among linked evidence.

### Conversion relevance

Use annotation-level conversion relevance, adjusted down when the evidence is passive bookmarking or generic dissatisfaction.

### Source convergence

A transparent option:

```text
0.7 * source coverage + 0.3 * source balance
```

Where:

```text
source coverage = distinct supporting source types / usable enabled source types
source balance = 1 - largest single-source share of supporting evidence
```

Avoid rewarding an opportunity only because one high-volume source dominates it.

### Segment concentration

Show whether the opportunity is unusually concentrated in a behavioral segment.

A transparent option is segment lift:

```text
(opportunity evidence in segment / all opportunity evidence)
/
(segment size / all retained evidence)
```

Normalize or cap the lift for the score while showing the raw lift in the UI.

### Evidence confidence

Combine:

- average annotation confidence
- exact-span validation rate
- human-review agreement where available

### Overall score

```text
Sum(component score * configured weight)
```

Every opportunity card must display all component scores and the weights used.

Also perform a simple sensitivity check. If small reasonable weight changes completely reorder the top opportunities, label the ranking unstable.

---

# 10. Behavioral Segmentation Requirements

Keep segments explainable and rule-based.

The most useful high-level map is:

```text
Purchase intent strength x decision activity
```

Possible dimensions:

- high, medium, low, or unclear intent
- active comparison versus passive saving
- frequent versus infrequent revisiting
- high versus low unresolved uncertainty
- on-platform versus off-platform research
- urgent versus non-urgent decision
- converted versus delayed versus abandoned

Do not force these exact segment names. Generate only segments supported by the data.

Each segment must show:

- human-readable name
- exact rule definition
- evidence count
- denominator
- share of eligible corpus
- overlap with other segments
- dominant behaviors
- dominant frictions
- off-platform activity
- stated workarounds
- confidence
- inspect evidence action

Use the label:

> **Candidate behavioral segments**

Do not use:

> **Proven Myntra customer personas**

---

# 11. Opportunity Generation Requirements

Generate opportunities from behavior + friction + consequence, not from feature ideas.

Preferred statement structure:

> Users with [intent or behavior] struggle to [complete a decision] because [evidenced unresolved need], leading them to [delay, abandon, compare elsewhere, forget, or use a workaround].

Every opportunity must include:

- neutral title
- opportunity statement
- affected segment
- affected stage
- evidence count and denominator
- seven-factor score
- supporting evidence count
- contradiction count
- adjacent evidence count
- source distribution
- representative verified quotes
- known limitations
- interview question
- disconfirming condition

Examples of acceptable statuses:

- Emerging hypothesis
- Shortlisted for interviews
- Confirmed by interviews
- Refined after interviews
- Challenged by interviews
- Rejected

Do not call the highest-ranked opportunity the `root cause` before interviews.

---

# 12. API Contract Required by the Interface

Preserve existing routes where possible, but make the following endpoints available or provide equivalent documented contracts.

## Metadata

```http
GET /api/health
GET /api/meta
```

`/api/meta` should return:

- app version
- analysis version
- taxonomy version
- ranking version
- configured AI provider/model label
- available sources
- public methodology note
- latest prepared-corpus run

## Overview and behaviors

```http
GET /api/dashboard/overview?scope=prepared_corpus
GET /api/dashboard/behaviours?scope=prepared_corpus
GET /api/dashboard/questions?scope=prepared_corpus
```

## Segments

```http
GET /api/segments?scope=prepared_corpus
GET /api/segments/{segment_id}/evidence
```

## Opportunities

```http
GET /api/opportunities?scope=prepared_corpus
GET /api/opportunities/{opportunity_id}
GET /api/opportunities/{opportunity_id}/evidence?relationship=support
```

## Evidence

```http
GET /api/evidence
GET /api/evidence/{evidence_id}
```

Supported evidence filters should include where available:

- source
- date range
- reason for saving
- intent
- purchase stage
- behavior
- friction
- severity
- off-platform channel
- workaround
- segment
- confidence
- human-review status
- opportunity relationship
- search text

Use pagination.

## Pipeline

```http
POST /api/pipeline/runs
GET /api/pipeline/runs/{run_id}
GET /api/pipeline/runs/latest
```

## Validation bridge

```http
GET /api/validation/survey
GET /api/validation/interviews
GET /api/validation/opportunities
```

Interview data may initially return an empty or `not_yet_available` state.

## Human review, protected

```http
POST /api/admin/annotations/{annotation_id}/reviews
PATCH /api/admin/annotations/{annotation_id}/reviews/{review_id}
```

Public endpoints must never expose private contact details or secrets.

---

# 13. Single Frontend Experience To Implement

Rebuild only the interface layer inside the existing frontend. Preserve the static frontend architecture. It is acceptable to split `app.js` into small modules if this improves maintainability, but do not migrate frameworks.

The frontend must support these states:

1. loading
2. connected to live backend
3. backend unavailable
4. prepared corpus available
5. no data yet
6. fresh sample queued
7. fresh sample running
8. completed
9. completed with warnings
10. failed
11. explicit demo mode

No screen should silently display fake success.

---

# 14. Visual Design Direction

Design this as a credible research-intelligence product with a fashion-commerce context, not as a consumer Myntra clone and not as a generic developer console.

## 14.1 Personality

- Evidence-led
- Premium but restrained
- Clear enough for a PM evaluator to understand in under five minutes
- Product insights before technical novelty
- Confident without overstating certainty

## 14.2 Palette

Retain Myntra-inspired pink as the primary accent, but use it selectively.

Suggested system:

- Background: deep charcoal/navy or clean warm off-white; keep one consistent theme
- Surface: high-contrast cards with subtle borders
- Primary accent: Myntra pink
- Secondary accent: muted violet
- Positive/status accent: teal
- Warning: amber
- Error: red
- Body text: high-contrast neutral
- Muted text: accessible gray

Do not rely on color alone for status. Add labels and icons.

## 14.3 Typography

Use the existing professional sans-serif family or another web-safe, readable family. Maintain clear hierarchy:

- Hero: 44-56 px desktop
- Page title: 28-36 px
- Section title: 20-24 px
- Card title: 15-18 px
- Body: 14-16 px
- Metadata: no smaller than 12 px

Avoid all-uppercase paragraphs and excessive letter spacing.

## 14.4 Layout

- Desktop-first at 1440 px
- Maximum readable width around 1280-1400 px
- Responsive at 1024, 768, and 390 px
- Consistent 8 px spacing system
- Card radius 12-16 px
- Moderate shadows and gradients only
- No dense glassmorphism that harms readability
- Sticky global header
- Clear navigation
- Accessible focus states

## 14.5 Icons and charts

- Use a consistent SVG icon set rather than emoji tabs
- Prefer horizontal bars, funnels, heatmaps, matrices, and compact trend cards
- Avoid decorative charts that do not answer a question
- Every chart displays its population and denominator
- Add tooltips or visible metric definitions

## 14.6 Motion

- Small entrance transitions
- Stage-progress animation driven by real polling state
- No fake timed animation claiming live work
- Respect reduced-motion preferences

---

# 15. Screen 1: Landing Page

The landing page must explain the engine before showing the dashboard.

## Header

Left:

- Brand mark
- `Myntra Wishlist Discovery Engine`

Right:

- Backend status
- Latest analysis date
- `Methodology`
- `Explore Analysis`

## Hero copy

### Eyebrow

```text
AI-powered product discovery research
```

### Main headline

```text
Turn public fashion conversations into evidence-backed wishlist opportunities.
```

### Supporting copy

```text
The engine analyzes public reviews and discussions to understand why saved items do or do not become purchases within 30 days - without assuming the answer in advance.
```

### Primary actions

- `Run Fresh Sample`
- `Explore Prepared Analysis`

### Integrity note

```text
Public conversations generate research hypotheses, not Myntra-wide causal proof. The final problem and MVP are validated through primary interviews.
```

## Business metric card

Title:

```text
Business metric this research supports
```

Metric:

```text
30-Day Wishlist-to-Purchase Conversion Rate
```

Formula:

```text
Users who purchase at least one wishlisted item within 30 days
/
Users who added at least one item to their wishlist
```

Note:

```text
The engine identifies behavioral opportunities beneath this metric. It does not calculate Myntra's private conversion rate.
```

## Process preview

Show the evidence chain:

```text
Public conversations
-> Clean evidence
-> Behavioral extraction
-> Candidate segments
-> Opportunity hypotheses
-> Interview validation
```

## Source and methodology preview

Show only actual configured or prepared-corpus sources. Each source card displays:

- source name
- collected count
- retained count
- last successful run
- status

Do not hard-code four active sources.

---

# 16. Screen 2: Run Fresh Sample Flow

Clicking `Run Fresh Sample` opens a modal or dedicated step.

## Pre-run view

Show:

- enabled sources returned by `/api/meta`
- disabled/unavailable sources with reason
- total item cap
- estimated scope wording, not a guaranteed duration
- explanation that the sample is separate from the prepared corpus
- cooldown status

Buttons:

- `Start Fresh Sample`
- `Cancel`

## After start

Receive a real `run_id` and transition to the Pipeline Progress screen.

Do not show a success alert and stop. The evaluator must see the actual process.

---

# 17. Screen 3: Pipeline Progress

Use a prominent nine-stage vertical or horizontal stepper.

Stages:

1. Collect public conversations
2. Normalize text
3. Mask personal information
4. Remove duplicates
5. Filter decision-relevant evidence
6. Extract behavior with AI
7. Validate evidence spans
8. Aggregate behavioral patterns
9. Rank opportunity hypotheses

Each stage card must show:

- status icon and text
- input count
- output count
- rejected count where applicable
- duration
- warning/error details

Also show source-level collection cards:

- source
- requested cap
- collected
- retained
- status
- warning

Use a concise event stream, not a wall of developer logs.

Example event messages:

```text
Google Play completed: 30 reviews collected.
Reddit unavailable: credentials not configured.
7 duplicates excluded.
18 items passed decision-relevance filtering.
15 of 18 AI annotations validated.
3 annotations flagged for review.
```

On terminal state:

- `View Fresh Sample Results`
- `Return to Prepared Analysis`

If partial success occurs, show `Completed with warnings`, not failure and not fake completion.

---

# 18. Dashboard Navigation

Use a clear side navigation on desktop and a compact top/dropdown navigation on mobile.

Recommended sections:

1. Overview
2. Discovery Questions
3. Behavior Explorer
4. Frictions & Workarounds
5. Candidate Segments
6. Opportunity Board
7. Evidence Library
8. Validation Bridge
9. Pipeline Runs
10. Methodology & Limits

The order mirrors the PM reasoning chain rather than the backend architecture.

---

# 19. Dashboard: Overview

## Dataset scope bar

At the top show:

- `Prepared Corpus`
- `Fresh Sample`
- selected run ID/date
- source scope
- analysis version

Changing scope must update every chart and denominator consistently.

## Main data cards

Show actual values:

- Raw conversations
- Unique after deduplication
- Decision-relevant evidence
- Valid AI annotations
- Human-reviewed annotations
- Active sources

Each card has a tooltip/definition.

## Retention funnel

Show:

```text
Raw
-> Unique
-> Non-noise
-> Relevance candidates
-> AI analyzed
-> Valid evidence
```

Display count and retention rate at every step.

## Source distribution

For each source show:

- raw count
- retained count
- retention rate
- share of final evidence
- last-run status

## Emerging hypotheses

Display the top three currently ranked opportunity hypotheses.

Use:

```text
Emerging hypothesis
```

not:

```text
Top root cause
```

Each card must show score, evidence count/denominator, confidence, and `Inspect evidence`.

## Limitations summary

Always show a compact limitations card:

- public conversations are self-selected
- source volumes are uneven
- absence of private conversion data
- findings require interview validation
- unclear/unclassified share

---

# 20. Dashboard: Discovery Questions

Create an 11-row coverage matrix based directly on the problem statement.

Columns:

- Number
- Discovery question
- Evidence coverage
- Top current signal
- Confidence
- Status
- Inspect

Statuses:

- Strong signal
- Directional signal
- Mixed evidence
- Insufficient evidence

Clicking a row opens a detail panel with:

- which fields answer the question
- count and denominator
- key distributions
- supporting evidence
- contradictory evidence
- source breakdown
- limitation

This screen is mandatory because it proves that the engine satisfies the brief rather than merely presenting generic sentiment charts.

---

# 21. Dashboard: Behavior Explorer

Organize this page around the wishlist journey.

## A. Why users save

Show reason-for-saving categories with:

- evidence count
- identifiable denominator
- retained-corpus coverage
- source mix

## B. Intent spectrum

Display an intent continuum:

```text
Passive inspiration
-> Buy later
-> Active comparison
-> Genuine consideration
-> Ready to purchase
```

Keep `unclear` visible.

## C. Decision stage

Show browsing, shortlisted, evaluating, resolving uncertainty, ready, delayed, abandoned, and purchased when supported.

## D. What happens after saving

Show multi-select post-save behaviors:

- revisit
- compare within Myntra
- compare elsewhere
- check reviews
- search externally
- ask someone
- add to bag
- wait
- forget
- buy elsewhere

Add the note:

```text
One evidence item may contain multiple behaviors; percentages may exceed 100%.
```

## E. Intent x action matrix

Create a heatmap showing intent level against decision activity. This becomes an explainable foundation for candidate segments.

Every chart must support click-through to evidence.

---

# 22. Dashboard: Frictions & Workarounds

## Friction overview

Show each friction with:

- evidence incidence
- high-intent incidence
- average severity
- average conversion relevance
- source count
- confidence

Do not rank only by count.

## Intent-friction matrix

This is more important than a simple friction bar chart.

Highlight situations where:

- intent is high
- proximity to purchase is near
- severity is medium/high
- users delay, abandon, or leave the platform

## Off-platform information seeking

Show:

- destination/channel
- what information was sought when identifiable
- affected stage
- associated friction
- outcome or workaround

## Workarounds

Show behaviors such as:

- buying elsewhere
- selecting another product
- asking another person
- searching video/social content
- waiting for price/stock
- returning later

## Purchase triggers and abandonment signals

Keep these in separate sections. Do not combine successful conversion triggers with reasons for abandonment.

---

# 23. Dashboard: Candidate Segments

Use a matrix visualization:

```text
Horizontal axis: decision activity
Vertical axis: purchase intent
```

Place candidate segments based on actual rules and evidence.

Each segment card includes:

- name
- rule
- count/denominator
- overlap note
- dominant reasons for saving
- dominant frictions
- off-platform behavior
- workarounds
- confidence
- relevance to the 30-day metric
- inspect evidence

Add a banner:

```text
These are explainable research segments derived from public evidence. They are not population estimates or final personas.
```

Do not automatically mark one as selected. A researcher may shortlist a segment for interviews later.

---

# 24. Dashboard: Opportunity Board

Use a ranked list, but make ranking transparent and challengeable.

Each opportunity card must include:

- rank
- neutral title
- full opportunity statement
- affected behavioral segment
- affected journey stage
- overall score
- seven component scores
- evidence count and denominator
- supporting evidence count
- contradictory evidence count
- adjacent evidence count
- source count and source balance
- confidence
- ranking stability
- status

Actions:

- `Inspect supporting evidence`
- `Inspect contradictions`
- `View score logic`
- `Add to interview shortlist` for protected researcher mode only

## Score-detail drawer

Explain every component in plain language:

```text
Frequency: 0.62 - 48 of 77 eligible evidence items
Severity: 0.71 - average severity 2.13/3
Purchase intent: 0.80 - evidence is concentrated among active/high-intent users
Conversion relevance: 0.76 - most items explicitly describe delay or abandonment
Source convergence: 0.58 - appears across 2 of 3 usable sources, with one source dominant
Segment concentration: 0.69 - 1.8x lift in active cross-platform comparers
Evidence confidence: 0.74 - 89% support-span validation, medium/high model confidence
```

Do not show made-up values. The above is format guidance only.

## Contradictory evidence

An opportunity cannot be evaluator-ready unless contradictory evidence is visible. Examples include:

- users who resolved the issue without abandoning
- high-intent users who converted despite the friction
- evidence suggesting a different cause
- source-specific patterns that do not converge

---

# 25. Dashboard: Evidence Library

Replace the current three mock evidence cards with a real paginated evidence interface.

## Table/list fields

- source
- date
- masked excerpt
- reason for saving
- intent
- decision stage
- friction
- behavior after saving
- confidence
- human-review status
- linked opportunity

## Filters

Use the API filters listed earlier.

## Evidence-detail drawer

Show:

- source and public URL
- published date
- masked full text
- exact highlighted support spans
- all AI-extracted fields
- support-span validation
- model/analysis version
- linked segment(s)
- linked opportunity relationship
- human-review status
- analyst note if public-safe

Do not expose raw PII. Do not expose private survey contacts.

---

# 26. Dashboard: Validation Bridge

This page connects the engine to the survey and later interviews while keeping evidence types separate.

Use three clearly separated layers.

## Layer 1: Public Evidence

Label:

```text
AI-analyzed public conversations
```

Show:

- corpus size
- sources
- opportunity hypotheses
- evidence confidence
- limitations

## Layer 2: Survey Pulse

Label:

```text
Directional convenience sample
```

Import or generate aggregates from:

```text
Fashion Shopping & Wishlist Habits - Quick Research (Responses).xlsx
```

Data-quality rules:

- retain raw response count
- calculate a separate eligible Myntra-recent-wishlist base
- flag exact/likely duplicates rather than silently counting them twice
- flag internally inconsistent rows
- show the actual denominator for each survey question
- keep personally identifying contact fields out of the public dashboard
- do not claim statistical representation
- do not merge survey percentages with public-evidence percentages

Useful survey signals to show dynamically include:

- reasons for wishlisting
- revisit frequency
- self-reported purchase likelihood
- recent wishlist conversion
- purchase triggers
- current unpurchased-item state
- non-purchase situation
- actions taken after wishlisting

Do not hard-code the current survey result values into the frontend. Generate a versioned aggregate snapshot.

## Layer 3: Interview Validation

Initially show:

```text
Interviews pending
```

After interviews, support per-opportunity results:

- untested
- confirmed
- refined
- challenged
- rejected

Display an evidence table:

| Opportunity hypothesis | Engine signal | Survey alignment | Interview finding | Decision |
|---|---|---|---|---|

## MVP decision gate

At the bottom, display:

```text
Final MVP decision remains locked until 5-6 interviews are complete, a target segment is justified, the root cause is evidenced, and existing workarounds are documented.
```

Do not build or display a final MVP recommendation inside the engine before this gate is met.

---

# 27. Dashboard: Pipeline Runs

Show a run history table with:

- run ID
- scope
- date/time
- sources
- requested cap
- raw count
- retained count
- AI success
- status
- duration
- warnings
- open details

Run detail uses the same real stage component as the Fresh Sample flow.

Do not expose secrets, internal stack traces, or raw credentials.

---

# 28. Dashboard: Methodology & Limits

Include an evaluator-friendly methodology page.

Sections:

1. Business metric
2. Public sources and collection policy
3. Cleaning, PII masking, and deduplication
4. AI extraction schema
5. Evidence-span validation
6. Behavioral segmentation
7. Opportunity scoring
8. Human review
9. Survey and interview separation
10. Known limitations

Use plain language. Link to technical API/docs only as secondary detail.

---

# 29. Frontend Implementation Rules

## 29.1 Remove implicit mock mode

Delete or isolate the current `MOCK_DATA` object.

If demo data is retained:

- place it in a separate `demo-data.js` file
- activate only with an explicit `?demo=1` query or build setting
- show a permanent `Illustrative demo data` banner
- prevent demo mode from claiming backend connection or a live run

## 29.2 Runtime configuration for Vercel

Add a lightweight static build process rather than hard-coding the Railway URL.

Recommended approach:

```text
frontend/
  package.json
  build.mjs
  config.template.js
  index.html
  app.js
  styles.css
  dist/
```

`build.mjs` should:

1. copy static assets into `dist`
2. generate `dist/config.js`
3. write only public configuration such as `API_BASE_URL`
4. never write secrets

The frontend reads:

```javascript
window.__APP_CONFIG__.API_BASE_URL
```

Configure Vercel:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `API_BASE_URL=https://<railway-domain>/api`

## 29.3 API client

Create one shared API wrapper with:

- base URL
- timeout
- JSON error handling
- abort controller
- typed/validated expected shapes where practical
- retry only for safe GET requests

## 29.4 Rendering safety

Escape all user-generated text before inserting it into HTML. Do not build evidence cards with unsafe raw `innerHTML` from source text.

## 29.5 Accessibility

- semantic landmarks
- keyboard navigation
- visible focus
- labelled form controls
- contrast compliance
- status text in addition to color
- aria-live region for pipeline progress
- reduced-motion support

---

# 30. Backend Refactor Map

Apply targeted changes in these files or equivalent modules.

## Existing files to modify

### `backend/app/main.py`

- remove production static-frontend responsibility or keep it dev-only
- configure allowed origins from environment
- register new routers
- add global error handling and request IDs where useful

### `backend/app/api/routes/pipeline.py`

- replace in-memory background trigger with DB-backed run creation
- return `run_id`
- add status and latest-run endpoints
- enforce caps/cooldown

### `backend/app/pipeline/pipeline.py`

- reuse current stages
- persist all processed outcomes
- update run-stage state
- save complete annotations
- support requested limits/sources
- support prepared and sample scopes
- capture source-specific failures

### `backend/app/pipeline/preprocessor.py`

- separate cleaned and masked text
- persist language and versions
- strengthen cross-run deduplication
- avoid over-narrow, hypothesis-biased keywords

### `backend/app/ai/schema.py`

- expand to problem-statement fields
- allow multi-valued behaviors and reasons
- preserve uncertainty outputs

### `backend/app/ai/prompts.py`

- update neutrality and evidence rules

### `backend/app/ai/provider.py`

- configurable model
- structured response validation
- bounded retries with rate-limit handling
- record provider/model/version

### `backend/app/scoring/aggregator.py`

- query direct structured fields
- calculate all required distributions and coverage metrics
- apply human-reviewed effective values
- remove `analysis_notes` parsing

### `backend/app/scoring/segments.py`

- make definitions configurable and evidence-inspectable
- disclose overlaps
- avoid causal assumptions in statements

### `backend/app/scoring/ranker.py`

- add segment concentration
- use actual evidence-level values
- add score stability/sensitivity
- link opportunity evidence

### `backend/app/config/ranking.yaml`

- add all seven factors and descriptions

### `backend/app/config/taxonomy.yaml`

- align with the expanded schema
- preserve emerging/other/unclear values

### `backend/app/config/sources.yaml`

- support source enablement, caps, and public-sample eligibility
- do not claim a disabled source is active

## New focused modules allowed

Add only where needed:

- `backend/app/worker.py`
- `backend/app/api/routes/meta.py`
- `backend/app/api/routes/evidence.py`
- `backend/app/api/routes/segments.py`
- `backend/app/api/routes/validation.py`
- `backend/app/api/routes/admin_reviews.py`
- `backend/app/services/run_service.py`
- `backend/app/services/effective_annotations.py`
- `backend/app/services/question_coverage.py`
- `backend/app/services/survey_snapshot.py`

Do not create a parallel second engine.

---

# 31. Findings Language Rules

Use these phrases:

- `Evidence suggests...`
- `Within the retained public-evidence corpus...`
- `X of Y eligible evidence items...`
- `Emerging opportunity hypothesis...`
- `Directional survey alignment...`
- `Requires primary interview validation...`
- `Mixed evidence...`
- `Insufficient evidence...`

Avoid these phrases unless primary research and evidence genuinely support them:

- `The root cause is...`
- `Myntra users generally...`
- `X% of Myntra users...`
- `This will increase conversion by...`
- `The data proves...`
- `The solution is...`

Every prominent finding must have:

- population definition
- numerator
- denominator
- scope/date
- confidence
- inspect-evidence action

---

# 32. Required Empty, Error, and Warning States

Implement polished states for:

## No prepared corpus

```text
No prepared analysis is available yet. Run the private/full corpus pipeline before publishing the evaluator dashboard.
```

## Backend unavailable

```text
The analysis service is temporarily unavailable. No research findings are being substituted with demo data.
```

## Source failure

```text
Reddit did not respond during this run. Results below use the successful sources only.
```

## AI partial failure

```text
4 of 22 candidate items could not be analyzed. They are excluded from annotation-based percentages and remain visible in the run audit.
```

## Insufficient evidence

```text
There is not enough direct evidence to answer this question confidently.
```

## Demo mode

```text
Illustrative demo dataset - not live research evidence.
```

These states are essential to evaluator trust.

---

# 33. Testing and Validation

Do not merely make the interface look complete. Verify that it is driven by actual API data.

## 33.1 Unit tests

Add/update tests for:

- expanded AI schema
- exact support-span validation
- separate cleaned/masked text
- cross-run deduplication
- stage count calculations
- denominator functions
- segment overlap
- seven-factor ranking
- survey snapshot cleaning
- effective human-reviewed annotations

## 33.2 Integration tests

Test:

- create sample run -> worker processes -> run status completes
- source partial failure -> completed with warnings
- raw item -> processed record regardless of rejection outcome
- valid annotation -> complete structured persistence
- opportunity -> linked support/contradictory evidence
- scope/run filters change endpoint denominators correctly

## 33.3 API tests

Verify:

- every public read endpoint returns a stable schema
- pagination works
- filters work
- no PII or secret leaks
- trigger caps and cooldown work
- protected admin routes reject unauthorized writes

## 33.4 Frontend tests/manual checks

Verify:

- no hard-coded analytics in production bundles
- API-down state does not show fake findings
- all data cards match API counts
- scope switching changes all screens consistently
- every major finding drills into evidence
- pipeline progress matches stored run stages
- percentages show denominators
- multi-select metrics explain sums above 100%
- mobile layout is usable
- keyboard and focus behavior work

## 33.5 Research-integrity audit

Pass all checks:

- no predetermined winning friction
- no target segment hard-coded into collection
- no feature recommendation produced by the engine
- no unsupported quote
- no hidden unclear rate
- no count inflated by duplicates
- no public-evidence/survey denominator mixing
- contradictory evidence visible
- public reviews described as hypothesis-generating

---

# 34. Deployment Requirements

## 34.1 Railway

Deploy the API and worker from the existing repository.

Environment variables may include:

```text
DATABASE_URL
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
GEMINI_API_KEY
GEMINI_MODEL
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
YOUTUBE_API_KEY
FRONTEND_ORIGINS
ADMIN_REVIEW_TOKEN
SAMPLE_RUN_MAX_ITEMS
SAMPLE_RUN_COOLDOWN_SECONDS
```

Do not expose values in logs or docs.

Required checks:

- `/api/health` succeeds
- DB connectivity is checked safely
- worker heartbeat updates
- one source failure does not crash the run
- Railway restart does not leave a run permanently marked running without recovery

## 34.2 Vercel

Deploy the static frontend separately.

Required checks from an incognito browser:

- landing page loads
- prepared analysis loads
- evidence drill-down works
- opportunity drill-down works
- fresh sample starts
- progress updates
- failed source is shown honestly
- no credentials appear in source or network responses
- no login required for public read-only evaluator access

## 34.3 Supabase

- apply additive migrations
- add indexes for dashboard queries
- keep service-role operations server-side
- enable suitable RLS if any direct public reads remain
- back up before migration

---

# 35. In-Place Implementation Phases

Do not restart at Phase 0 of the original project. Use these refinement phases against the current implementation.

## Refinement Phase A: Baseline audit and safety

Tasks:

- create a backup branch or commit
- inventory current files and routes
- remove secrets from tracked/shared artifacts
- compare docs with code
- identify existing tests and baseline status
- document current working behavior

Exit criteria:

- no secret is committed
- current behavior is documented
- no working component is removed without justification

## Refinement Phase B: Data contract and persistence completion

Tasks:

- add migration 0002
- expand AI schema
- persist all fields
- persist processed rows for every raw item
- implement exact-span validation
- separate cleaned and masked text
- implement effective reviewed annotations

Exit criteria:

- one evidence item can be traced from raw text through effective annotation
- all required fields are queryable directly
- no structured value depends on parsing `analysis_notes`

## Refinement Phase C: Real run orchestration

Tasks:

- DB-backed run queue
- worker
- per-stage status
- source caps
- fresh sample cooldown
- prepared/fresh scopes
- status endpoints

Exit criteria:

- `POST /api/pipeline/runs` returns a run ID
- the frontend can poll real progress
- no fake stage sequence is needed

## Refinement Phase D: Metrics, questions, segments, and opportunities

Tasks:

- denominator-aware aggregation
- 11-question coverage
- explainable overlapping segments
- seven-factor scoring
- opportunity evidence linking
- contradictory evidence
- sensitivity check

Exit criteria:

- multiple opportunities are ranked from real stored evidence
- every score is explainable
- every important finding drills into evidence

## Refinement Phase E: Interface redesign

Tasks:

- landing page
- fresh sample flow
- live pipeline progress
- complete dashboard screens
- evidence drawer
- validation bridge
- methodology/limitations
- loading/error/demo states

Exit criteria:

- an evaluator can understand raw evidence -> behavioral pattern -> segment -> opportunity without reading code
- no hard-coded production finding remains

## Refinement Phase F: Survey bridge

Tasks:

- create survey aggregate importer/snapshot
- clean and flag duplicates/inconsistencies
- exclude contact details from public output
- show separate survey denominators
- prepare interview-validation placeholders

Exit criteria:

- survey signals can align with or challenge engine hypotheses without being merged into engine counts

## Refinement Phase G: Deployment and evaluator QA

Tasks:

- Railway API
- Railway worker
- Vercel frontend
- production envs
- CORS/security
- incognito test
- bounded fresh sample test

Exit criteria:

- public evaluator experience works end to end
- prepared corpus remains stable even if a fresh source fails
- no secret or fake live state is exposed

---

# 36. Required Documentation Updates

Update the existing documentation after implementation.

## `README.md`

Correct it to describe:

- vanilla HTML/CSS/JavaScript frontend on Vercel
- FastAPI API and worker on Railway
- Supabase PostgreSQL
- Gemini structured analysis
- local setup
- deployment
- public versus admin routes

## `decisions.md`

Append each refinement decision with:

- date
- decision
- reason
- trade-off
- files affected

## New report

Create:

```text
ENGINE_REFINEMENT_REPORT.md
```

Include:

- current-state issues found
- changes made
- migrations
- API changes
- metric definitions
- UI changes
- tests run and exact results
- live deployment URLs
- known limitations
- next research step

Do not claim a test passed unless it was actually run.

---

# 37. Mandatory Final Acceptance Checklist

The refinement is complete only when every applicable item below passes.

## Existing project continuity

- [ ] Existing repository retained
- [ ] Existing connectors reused
- [ ] Existing preprocessing/pipeline/scoring foundations reused
- [ ] No unnecessary framework migration
- [ ] Changes documented

## Data integrity

- [ ] Raw source text preserved privately
- [ ] Masked text used publicly
- [ ] Every raw item has a processed outcome
- [ ] Cross-run duplicates excluded
- [ ] All AI fields persisted structurally
- [ ] Exact support spans validated
- [ ] Original AI output preserved after human override

## Problem-statement coverage

- [ ] All 11 discovery questions visible
- [ ] Why users save is shown
- [ ] Intent versus bookmarking is shown
- [ ] Purchase blockers/uncertainties are shown
- [ ] Delay behavior is shown
- [ ] Post-save journey is shown
- [ ] Comparison behavior is shown
- [ ] Off-platform information seeking is shown
- [ ] Workarounds are shown
- [ ] Behavioral segments are shown
- [ ] Opportunities tied to 30-day conversion are ranked

## Metrics

- [ ] No estimated raw count
- [ ] Every percentage has a denominator
- [ ] Unclear rate is visible
- [ ] Multi-select percentages are explained
- [ ] Seven opportunity factors implemented
- [ ] Segment concentration implemented
- [ ] Ranking sensitivity exposed

## Evidence

- [ ] Every major finding drills into evidence
- [ ] Quotes are exact source spans
- [ ] Supporting evidence visible
- [ ] Contradictory evidence visible
- [ ] Confidence and limitations visible

## Pipeline

- [ ] Fresh sample creates a real run
- [ ] Run returns a run ID
- [ ] Stage progress is real
- [ ] Counts and durations are real
- [ ] Source failures are visible
- [ ] Caps and cooldown work
- [ ] Prepared corpus remains separate

## Interface

- [ ] Landing page explains the metric and engine
- [ ] Fresh sample flow works
- [ ] Pipeline progress works
- [ ] Dashboard answers the brief
- [ ] Evidence library works
- [ ] Validation bridge separates evidence layers
- [ ] No implicit demo data
- [ ] Responsive and accessible

## Research integrity

- [ ] No predetermined root cause
- [ ] No final MVP selected by the engine
- [ ] No public-review findings described as causal proof
- [ ] Survey is labelled directional
- [ ] Survey contacts are private
- [ ] Interviews may confirm, refine, or challenge findings

## Deployment

- [ ] Frontend deployed to Vercel
- [ ] API deployed to Railway
- [ ] Worker deployed/running on Railway
- [ ] Supabase migrations applied
- [ ] CORS restricted
- [ ] Secrets server-side only
- [ ] Incognito evaluator test passed

---

# 38. Exact Instruction To Begin Work

Use this as the first implementation instruction after placing this file in the repository root:

```text
Read this file completely, followed by the source-of-truth documents in the specified order. This is an in-place refinement of the existing Myntra Review/Discovery Engine, not a rebuild.

First inspect the current repository and produce a concise delta plan mapping every required change to the existing files. Preserve working connectors, preprocessing, pipeline, database, scoring, tests, and the vanilla frontend. Do not migrate frameworks or create a parallel engine.

Then implement Refinement Phases A through G sequentially. Do not retain hard-coded production findings, estimated counts, automatic mock fallback, or simulated live pipeline logs. The frontend must deploy on Vercel, the FastAPI API and persistent pipeline worker must deploy on Railway, and Supabase must remain the system of record.

Every finding must show a count, denominator, scope, confidence, and inspectable source evidence. All 11 discovery questions in the problem statement must be answered or explicitly marked as insufficient evidence. Public reviews, survey results, and interview findings must remain separate evidence layers. The engine must output prioritized opportunity hypotheses for interviews, not a final MVP or an unvalidated root cause.

After each phase, report: files changed, behavior added, tests run, exact results, unresolved issues, and whether the phase exit criteria passed. Never claim live data, a successful test, a deployed service, or a research finding unless it is genuinely verified.
```

---

# 39. Final Product Story The Interface Must Communicate

At the end of this refinement, an evaluator should be able to open one URL and understand this sequence without reading the repository:

```text
We are trying to improve 30-day wishlist-to-purchase conversion.

The engine collected public fashion-shopping conversations from disclosed sources.

It cleaned, masked, deduplicated, and filtered them.

Gemini converted relevant evidence into structured behavior, intent, friction, workaround, and confidence fields.

The system showed what it could and could not infer.

It generated explainable candidate behavioral segments.

It ranked multiple opportunity hypotheses using seven transparent factors rather than mention volume alone.

Every important finding could be traced to exact source evidence and contradictory evidence.

A separate survey layer showed directional alignment or disagreement.

The opportunity hypotheses were handed to 5-6 interviews for validation.

Only after interviews would the project define the root cause and choose the final MVP.
```

That is the required engine experience. Improve the current implementation until this story is true in the code, the data, and the interface.
