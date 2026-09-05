# Myntra Wishlist AI Discovery Engine - Implementation Plan

## 1. Purpose of This Document

This document defines the **phase-wise implementation plan** for the Myntra Wishlist AI Discovery Engine described in:

1. `problem statement.md`
2. `architecture.md`

It is an execution plan for the **Discovery Engine only**. It does not define the final graduation-project MVP.

The implementation must remain research-neutral. No phase should hard-code a preferred problem such as fit, price, size, reviews, styling, or any future feature idea.

The engine is complete only when it can move from:

**Public evidence -> cleaned evidence -> structured behavioural analysis -> behavioural patterns -> opportunity comparison -> inspectable evidence -> primary-research hypotheses**

---

## 2. Implementation Principles

These rules apply throughout the build.

1. **Build the evidence chain before the dashboard polish.**
2. **Use deterministic logic where deterministic logic is sufficient.**
3. **Use AI only for semantic interpretation.**
4. **Every important AI interpretation must remain traceable to source evidence.**
5. **Never fabricate quotes or unsupported intent.**
6. **Every percentage must expose its denominator.**
7. **Duplicates must not inflate findings.**
8. **Opportunity ranking must use multiple dimensions, not mention count alone.**
9. **Contradictory evidence must remain visible.**
10. **The engine outputs research opportunities, not final product features.**
11. **The evaluator sample run must execute a real bounded pipeline run.**
12. **Do not move to the next phase until the current phase exit criteria pass.**

---

## 3. Deployment Strategy for Implementation

The architecture defines a production-like path using:

- Next.js / React on Vercel
- Supabase PostgreSQL
- Python/FastAPI backend
- AI provider abstraction
- optional scheduled automation

For implementation, use the **leanest working deployment path first**.

### Default path

Start with:

- **Vercel** - dashboard/frontend
- **Supabase** - PostgreSQL, storage if required, and lightweight server-side functions where practical
- **Gemini or another approved LLM provider** - semantic analysis through a provider abstraction

### Add Railway only if required

Introduce **Railway + FastAPI** only if one or more of these become true:

- scraping jobs exceed serverless execution limits
- AI batch processing needs longer-running workers
- background jobs need reliable process control
- Python libraries required by connectors cannot run comfortably in the selected serverless environment
- the evaluator sample run cannot be implemented reliably without a persistent backend

### Add GitHub Actions only if required

Introduce **GitHub Actions** only if scheduled or manual full-corpus runs need an external trigger that Supabase/Vercel scheduling cannot reliably provide.

The architecture boundaries should remain the same even if the deployment services are simplified.

**Decision checkpoint:** finalize the backend hosting choice after Phase 6, once real connector and pipeline execution times are known.

---

# PHASE 0 - Project Bootstrap and Guardrails

## Goal

Create a clean repository and prevent the build from drifting away from the approved problem statement and architecture.

## Tasks

- [ ] Create/confirm repository root: `myntra-grad-project/`
- [ ] Add the existing documents:
  - `problem statement.md`
  - `architecture.md`
  - `implementation plan.md`
- [ ] Create the base project structure from `architecture.md`.
- [ ] Initialize Git.
- [ ] Create `.gitignore`.
- [ ] Add `.env.example` containing variable names only.
- [ ] Ensure `.env`, credentials, service-role keys, API keys, and database passwords are excluded from Git.
- [ ] Create a minimal `README.md` with project purpose and local setup placeholders.
- [ ] Create configuration placeholders:
  - `taxonomy.yaml`
  - `ranking.yaml`
  - `sources.yaml`
- [ ] Record an initial `analysis_version`, `processing_version`, and `source_config_version`.

## Initial Repository Structure

```text
myntra-grad-project/
|
+-- problem statement.md
+-- architecture.md
+-- implementation plan.md
+-- README.md
+-- .env.example
+-- .gitignore
|
+-- backend/
|   +-- app/
|   |   +-- connectors/
|   |   +-- pipeline/
|   |   +-- ai/
|   |   +-- scoring/
|   |   +-- db/
|   |   +-- config/
|   +-- tests/
|
+-- frontend/
|
+-- database/
|   +-- migrations/
|
+-- research/
|   +-- validation_set/
|   +-- human_review/
|
+-- scripts/
```

## Test Criteria

- Repository starts without missing-file errors.
- No secrets are committed.
- Configuration files load successfully.
- Project documents are present and readable.

## Exit Criteria

Phase 0 passes when the project can be cloned/opened and another agent can understand the intended system boundaries from the three core markdown files.

---

# PHASE 1 - Database Schema and Evidence Contracts

## Goal

Create the data foundation before building scrapers or AI logic.

## Tasks

Create Supabase/PostgreSQL migrations for:

- [ ] `collection_runs`
- [ ] `raw_evidence`
- [ ] `processed_evidence`
- [ ] `evidence_annotations`
- [ ] `human_reviews`
- [ ] `opportunities`
- [ ] `opportunity_evidence`

Implement the field definitions from `architecture.md`.

### Required design rules

- Raw source evidence remains immutable.
- Cleaned/masked evidence is stored separately.
- AI annotations are versioned.
- Human overrides never overwrite the original AI output.
- Opportunity evidence supports `supports`, `contradicts`, and `adjacent` relationships.
- Source items have stable/idempotent keys.
- Duplicate records remain traceable.

## Data Contracts

Create typed internal models for at least:

- `RawEvidence`
- `ProcessedEvidence`
- `EvidenceAnnotation`
- `CollectionRun`
- `Opportunity`
- `OpportunityEvidence`

Use Pydantic or an equivalent typed schema if Python is used.

## Seed Data

- [ ] Add 15-25 manually created/sample evidence rows covering:
  - relevant wishlist behaviour
  - generic app complaints
  - comparison behaviour
  - unclear intent
  - duplicate content
  - off-platform research
  - contradictory evidence
- [ ] Do not make all seed examples support one suspected problem.

## Test Criteria

- Migrations run successfully on a clean database.
- Seed records insert successfully.
- Raw and processed evidence remain separate.
- Re-running the same seed/import does not create duplicate source records.
- Human override records do not modify original annotations.

## Exit Criteria

Phase 1 passes when the complete evidence chain can be represented in the database without losing the source text or the distinction between deterministic processing, AI interpretation, and human review.

---

# PHASE 2 - Source Connector Foundation

## Goal

Build a reusable connector layer and prove that real public evidence can enter the system.

## Tasks

### 2.1 Common connector interface

Implement a shared connector contract similar to:

```python
class SourceConnector:
    source_name: str

    def collect(self, since=None, limit=None) -> list[RawEvidence]:
        ...
```

Every connector must normalize output into the same `RawEvidence` structure.

### 2.2 Build sources in priority order

Build the easiest and most reliable sources first.

**Priority A - required for first end-to-end run**

- [ ] Google Play Store Myntra reviews
- [ ] One long-form/public conversation source with richer decision behaviour, preferably Reddit or another legally accessible public source

**Priority B - add after Priority A is stable**

- [ ] Apple App Store
- [ ] YouTube comments via permitted API/access method

**Priority C - optional/extensible**

- [ ] Approved public URL importer
- [ ] Other public forums where technically and legally accessible

### 2.3 Metadata preservation

Store where available:

- `source_type`
- `source_item_id`
- `source_url`
- `published_at`
- `collected_at`
- `rating`
- `parent_context`
- `source_metadata`
- `collection_run_id`

### 2.4 Compliance rules

Do not bypass:

- authentication
- CAPTCHAs
- anti-bot protections
- paywalls
- access restrictions

If a source is unreliable or not legally/technically suitable, remove it rather than engineering around the restriction.

## Test Criteria

For each enabled connector:

- returns real public evidence
- emits normalized objects
- preserves stable source IDs where possible
- respects item limits
- handles empty results safely
- handles network/source failure without crashing the whole pipeline
- can be rerun without duplicating existing source items

## Exit Criteria

Phase 2 passes when at least **two useful source types** can reliably populate `raw_evidence`, including at least one source likely to contain richer purchase-decision context than short app-store reviews.

---

# PHASE 3 - Deterministic Preprocessing Pipeline

## Goal

Clean the corpus and protect downstream AI analysis from noise, duplicates, and obvious PII.

## Tasks

Implement:

### 3.1 Text normalization

- [ ] whitespace normalization
- [ ] HTML cleanup
- [ ] repeated punctuation cleanup
- [ ] original raw text preservation
- [ ] meaningful emoji preservation where useful

### 3.2 Language handling

- [ ] detect language
- [ ] retain original text
- [ ] define how supported non-English evidence will be analyzed or translated

### 3.3 PII masking

Mask obvious:

- [ ] phone numbers
- [ ] email addresses
- [ ] addresses where clearly identifiable
- [ ] order/account identifiers
- [ ] other obvious unnecessary personal data

### 3.4 Spam/noise rules

Detect/remove/down-rank:

- [ ] empty content
- [ ] promotional spam
- [ ] copy-paste repetition
- [ ] clearly unrelated content
- [ ] pure service/logistics complaints with no useful purchase-decision evidence

### 3.5 Duplicate detection

Implement:

1. exact normalized hash matching
2. near-duplicate detection using similarity/embeddings only if necessary

Duplicates remain traceable but are excluded from independent frequency counts.

### 3.6 Stage-A relevance candidate filter

Use configurable keywords/metadata only as a **cheap candidate filter**.

Do not use these rules to declare the final theme or root cause.

## Test Criteria

Create unit tests for:

- normalization
- PII masking
- exact duplicate detection
- near-duplicate behaviour where implemented
- spam handling
- deterministic relevance-candidate rules

Manually inspect a sample of processed evidence.

## Exit Criteria

Phase 3 passes when a raw corpus can be transformed into a clean, masked, duplicate-aware candidate corpus while preserving auditability back to every raw item.

---

# PHASE 4 - AI Analysis Schema, Prompting, and Validation Set

## Goal

Build the semantic interpretation layer without allowing the model to invent unsupported user behaviour.

## Tasks

### 4.1 Create strict AI schema

Implement fields from `architecture.md`, including:

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
- `frictions`
- `emerging_themes`
- `intent_strength`
- `severity`
- `conversion_relevance`
- `proximity_to_purchase`
- `segment_signals`
- `evidence_confidence`
- `supporting_spans`

Every ambiguous field must support:

- `unclear`
- `not_applicable`

### 4.2 Configure taxonomy

Create `taxonomy.yaml` with the initial categories listed in the problem statement, while preserving:

- `other`
- `emerging_theme`
- `unclear`

The taxonomy is a starting vocabulary, not a list of conclusions.

### 4.3 AI provider abstraction

Create an adapter interface so models can be changed without altering pipeline logic.

Evaluate candidate models using the same fixed validation set.

Select the model based on:

- structured JSON reliability
- support-span accuracy
- hallucination rate
- semantic usefulness
- latency
- cost/rate limits

### 4.4 Prompt rules

Prompts must explicitly instruct the model to:

- extract only what the text supports
- prefer `unclear` over inference
- separate behaviour from sentiment
- identify emerging themes when appropriate
- return source-supported spans
- not generate product solutions
- not infer demographics unless explicitly stated and genuinely relevant
- not treat every wishlist mention as genuine purchase intent

### 4.5 Build human validation set

Manually label approximately **30-50 representative evidence items** across multiple sources.

Include:

- clear relevant evidence
- weak/ambiguous evidence
- unrelated complaints
- high-intent evidence
- passive saving/bookmarking evidence
- comparison behaviour
- workaround/off-platform behaviour
- contradictory cases
- emerging themes

### 4.6 Validation functions

Implement:

- strict schema validation
- evidence-span existence validation
- retry policy for malformed outputs
- failed-analysis status after bounded retries
- version storage for model/prompt/schema

## Test Criteria

On the validation set, manually review:

- relevance classification
- intent extraction
- friction/theme extraction
- workaround extraction
- support-span correctness
- inappropriate inference
- `unclear` usage

Do not require academic benchmark scores, but record known weaknesses.

## Exit Criteria

Phase 4 passes when the AI can produce valid structured annotations whose important claims can be traced to real source spans and when obvious unsupported interpretations are rejected or marked unclear.

---

# PHASE 5 - End-to-End Enrichment Pipeline

## Goal

Connect collection, preprocessing, relevance classification, AI enrichment, and persistence into one real pipeline.

## Tasks

Implement the pipeline in this order:

```text
Create collection run
        -> collect evidence
        -> save raw evidence
        -> normalize / mask PII
        -> deduplicate
        -> deterministic relevance candidate filter
        -> AI relevance classification
        -> AI behavioural enrichment
        -> validate output / evidence spans
        -> save annotations
        -> complete run with counts and warnings
```

### Required run metadata

Capture:

- source start/end
- source item count
- raw item count
- duplicate count
- candidate/relevance count
- retained evidence count
- AI success count
- AI failure count
- duration per stage
- model/analysis version
- warnings/errors

### Incremental processing

Do not re-analyze an unchanged item unless:

- prompt/schema version changes
- taxonomy version changes
- source text changes
- reviewer requests re-analysis

Cache by evidence/content hash + analysis version.

### Failure handling

- one source failure does not cancel all other sources
- AI failures use bounded retry/backoff
- no placeholder annotations are written
- partial runs are marked with warnings

## Test Criteria

Run at least three end-to-end test runs:

1. **tiny run** - approximately 10-20 raw items
2. **medium run** - approximately 100-250 raw items
3. **failure run** - intentionally fail one connector/API dependency and verify graceful degradation

## Exit Criteria

Phase 5 passes when real public evidence can travel from a connector to a valid stored AI annotation without manual intervention and every run exposes real counts, failures, and versions.

---

# PHASE 6 - Aggregation, Behavioural Segments, and Opportunity Ranking

## Goal

Turn individual evidence annotations into transparent product-research findings.

## Tasks

### 6.1 Deterministic aggregation

Calculate from stored structured evidence:

- raw evidence count
- retained relevant evidence count
- source distribution
- relevance rate
- reason-for-saving distribution
- wishlist-intent distribution
- post-save behaviour distribution
- purchase-stage distribution
- friction/uncertainty distribution
- off-platform research patterns
- workaround patterns
- intent x friction matrix
- friction x purchase-stage matrix
- segment-signal counts
- source convergence

Every percentage output must contain:

- numerator/count
- denominator
- percent
- population definition

### 6.2 Explainable behavioural segment candidates

Start with rule-based combinations of structured fields.

Potential dimensions include:

- high vs low intent
- active comparison vs passive saving
- high vs low unresolved uncertainty
- frequent vs low revisit
- off-platform dependence
- urgent vs low-urgency decision
- delayed vs abandoned behaviour

Do not hard-code the final target segment.

### 6.3 Opportunity candidate generation

Generate opportunities in the format:

> Users with [behaviour / intent] struggle to [complete desired behaviour] because [observed friction / uncertainty], causing [delay / comparison / abandonment / workaround].

Require a minimum evidence threshold before an opportunity is promoted.

### 6.4 Opportunity evidence mapping

Map evidence to each opportunity as:

- supports
- contradicts
- adjacent

### 6.5 Transparent ranking

Implement configurable `ranking.yaml` using the architecture dimensions:

- frequency
- severity
- purchase intent
- conversion relevance
- source convergence
- segment concentration
- evidence confidence

Use deterministic arithmetic for the final score.

Display/store both:

- overall score
- component scores

### 6.6 Weight sensitivity check

Test whether small reasonable changes in ranking weights completely reorder the top opportunities.

If rankings are highly unstable, flag this rather than presenting the ranking as precise.

## Test Criteria

- duplicate evidence does not inflate frequency
- every percentage exposes a denominator
- overall score recomputes correctly from config weights
- changing `ranking.yaml` changes scores without code changes
- opportunities have inspectable supporting evidence
- contradictory evidence can be stored and displayed
- at least two competing opportunity areas emerge from test data where evidence supports them

## Exit Criteria

Phase 6 passes when the engine produces multiple evidence-backed, inspectable opportunity hypotheses and can explain why Opportunity A ranks above Opportunity B without relying only on mention volume.

---

# PHASE 7 - Backend/API and Hosting Decision Checkpoint

## Goal

Expose the analysis through stable endpoints and choose the leanest backend deployment that can run the real workload.

## Tasks

Implement equivalent endpoints/functions for:

### Health / metadata

- [ ] `GET /api/health`
- [ ] `GET /api/meta`

### Dashboard

- [ ] summary
- [ ] patterns
- [ ] segments

### Evidence

- [ ] evidence list
- [ ] evidence detail
- [ ] filters by source/date/friction/intent/stage/severity/confidence where implemented

### Opportunities

- [ ] opportunity list
- [ ] opportunity detail
- [ ] opportunity evidence

### Pipeline

- [ ] sample-run trigger
- [ ] run status

### Human review

- [ ] flag annotation
- [ ] override annotation

Protect write/admin actions.

## Hosting Decision Test

Run a real medium pipeline and measure:

- connector execution time
- preprocessing time
- AI batch time
- total execution time
- memory/runtime needs
- sample-run response behaviour

### Choose one path

**Path A - Supabase/Vercel only**

Use if the workload runs reliably within practical serverless/background execution limits.

**Path B - Railway FastAPI worker**

Use if long-running scraping/batch processing needs a persistent Python backend.

The frontend and database contracts should remain unchanged whichever path is selected.

## Test Criteria

- all read endpoints return valid typed payloads
- public payloads never expose raw secrets or unnecessary PII
- database service-role keys never reach the frontend
- filters return correct denominator-aware data
- write endpoints are protected
- a real pipeline workload determines hosting choice, not preference alone

## Exit Criteria

Phase 7 passes when the engine has stable API boundaries and the backend hosting choice has been justified by observed workload behaviour.

---

# PHASE 8 - Discovery Dashboard

## Goal

Build an evaluator-facing dashboard that makes the evidence-to-opportunity chain easy to understand.

## Tasks

Create the following screens/views.

### 8.1 Overview

Show:

- total raw evidence
- retained relevant evidence
- source count/distribution
- most recent run
- analysis version
- high-level behavioural findings

### 8.2 Behaviour Explorer

Show:

- reasons for saving where identifiable
- purchase-intent patterns
- post-save behaviour
- purchase/decision stage
- major frictions/uncertainties
- off-platform research
- workarounds

All percentages show count + denominator.

### 8.3 Segment Explorer

Show explainable behavioural segment candidates and how their evidence differs.

Do not claim statistical representation of the entire Myntra user base.

### 8.4 Opportunity Board

For each opportunity show:

- opportunity statement
- overall score
- component scores
- evidence count
- source count
- strongest segment signal
- representative evidence
- contradictory evidence count
- evidence confidence

### 8.5 Evidence Drill-Down

Allow a user to inspect:

- masked evidence span
- source type
- date
- behavioural annotations
- confidence
- link to opportunity
- support/contradict/adjacent relationship

### 8.6 Pipeline View

Show actual stages:

```text
Collect -> Clean -> Deduplicate -> Relevance -> Analyze -> Aggregate -> Rank
```

Display actual:

- status
- counts
- duration
- warnings/errors

## UI Principles

- Product insight first; technical novelty second.
- Do not overwhelm the evaluator with engineering logs.
- Avoid unsupported causality language.
- Clearly label public-review findings as discovery hypotheses.
- Do not display unmasked PII.

## Test Criteria

- dashboard loads without hard-coded analytics
- changing database findings changes the UI
- every major finding can drill into evidence
- opportunity component scores are visible
- contradictory evidence is discoverable
- all percentages expose denominators
- mobile/tablet layout is usable enough for evaluation

## Exit Criteria

Phase 8 passes when an evaluator can understand how collected conversations became behavioural patterns and ranked opportunities without reading the source code.

---

# PHASE 9 - Human Review and Research-Integrity QA

## Goal

Prove that the engine is inspectable and reduce the risk of AI-driven confirmation bias.

## Tasks

Implement reviewer workflow:

1. open evidence
2. inspect masked text + AI annotation
3. accept, flag, or correct
4. store override separately
5. aggregation prefers reviewed value where appropriate
6. preserve original AI output

### Review sample

Manually review:

- [ ] random annotations
- [ ] evidence supporting top opportunities
- [ ] low-confidence items
- [ ] contradictory items
- [ ] emerging-theme items
- [ ] high-severity/high-conversion-relevance items

### Research-integrity checks

Verify:

- [ ] taxonomy includes `other`, `emerging_theme`, and `unclear`
- [ ] no prompt tells the AI which theme should win
- [ ] no final target segment is embedded in source filters
- [ ] no opportunity is ranked only by mentions
- [ ] percentages have denominators
- [ ] duplicates are excluded from independent counts
- [ ] quotes are source spans, not generated text
- [ ] public evidence is described as hypothesis-generating, not causal proof
- [ ] final output remains opportunity statements, not feature recommendations

## Test Criteria

Record a simple QA summary:

- sample reviewed
- obvious annotation errors
- corrected fields
- common failure modes
- known blind spots

## Exit Criteria

Phase 9 passes when the top findings have been manually inspected and the team can state both what the engine appears to show and where its evidence is weak.

---

# PHASE 10 - Real Evaluator Sample Run

## Goal

Allow an evaluator to trigger a small **real** pipeline run without putting the full system at risk.

## Tasks

Implement a public action such as:

> **Run Fresh Sample**

The action must:

1. create a real pipeline run
2. collect a capped fresh/recent sample from one or more reliable sources
3. persist raw evidence
4. preprocess and deduplicate
5. run relevance filtering
6. run AI enrichment on retained items
7. validate/store annotations
8. calculate sample findings
9. expose genuine run progress/status

### Safety limits

Implement:

- strict item cap
- cooldown/rate limit
- AI request/token cap
- timeout handling
- only reliable public permitted sources
- protection against repeated expensive requests

The main dashboard should continue to use the larger prepared corpus so a live source failure does not destroy the evaluator experience.

## Test Criteria

- sample run produces new database records
- counts reflect real stages
- no simulated/fake log sequence is used
- cooldown works
- one source failure produces a visible warning, not a fake success
- evaluator cannot trigger unrestricted full-corpus processing

## Exit Criteria

Phase 10 passes when an evaluator can trigger and observe a bounded real run from collection through analysis.

---

# PHASE 11 - Production Deployment and Automation

## Goal

Deploy a stable public engine and add only the automation infrastructure actually needed.

## Tasks

### 11.1 Frontend

- [ ] Deploy Next.js dashboard to Vercel.
- [ ] Configure production environment variables.
- [ ] Confirm public read-only evaluator access.

### 11.2 Database

- [ ] Create/confirm production Supabase project.
- [ ] Apply production migrations.
- [ ] Configure secure service credentials server-side only.
- [ ] Configure appropriate RLS/access rules if the frontend accesses Supabase directly for safe read operations.

### 11.3 Backend

Deploy using the hosting decision from Phase 7:

- Supabase/Vercel server-side functions if sufficient, **or**
- Railway FastAPI/pipeline worker if required.

### 11.4 Scheduling

First try the simplest supported scheduler.

Add GitHub Actions only if it materially improves reliability for:

- nightly full-corpus processing
- manual workflow dispatch
- scheduled backend trigger

Do not add GitHub Actions merely because the previous Spotify project used it.

### 11.5 Environment and security QA

- [ ] no `.env` committed
- [ ] rotate any accidentally exposed keys immediately
- [ ] frontend bundle contains no service-role keys
- [ ] evaluator write access is limited to controlled sample-run action
- [ ] human-review/admin writes are protected

## Test Criteria

From an incognito/logged-out browser:

- public dashboard loads
- charts/data load
- evidence drill-down works
- opportunity drill-down works
- sample run starts and reports genuine status
- no login is required for evaluator viewing unless explicitly unavoidable
- no secret appears in page source or network payloads

## Exit Criteria

Phase 11 passes when the deployed production URL provides the complete evaluator experience reliably.

---

# PHASE 12 - Full-Corpus Run, Research Output, and Handoff

## Goal

Produce the evidence-backed discovery output that will feed participant selection and primary research.

## Tasks

### 12.1 Run production corpus

- [ ] collect from all stable enabled sources
- [ ] preprocess/deduplicate
- [ ] analyze relevant evidence
- [ ] manually inspect high-impact findings
- [ ] aggregate behavioural patterns
- [ ] generate competing opportunities
- [ ] calculate transparent scores

### 12.2 Create a findings snapshot

Record for the graduation project:

- total raw conversations
- retained relevant evidence
- source distribution
- reasons for wishlisting where identifiable
- intent patterns
- post-save behaviour
- major uncertainties/frictions
- off-platform behaviours/workarounds
- segment signals
- opportunity scores
- top supporting evidence
- contradictory evidence
- confidence/limitations
- analysis version and run date

### 12.3 Generate interview hypotheses

For the strongest competing opportunities, create a research table:

| Opportunity hypothesis | Engine evidence | What interviews must validate | What would challenge it |
|---|---|---|---|
| Opportunity A | Evidence summary | Behaviour/root-cause questions | Disconfirming evidence |
| Opportunity B | Evidence summary | Behaviour/root-cause questions | Disconfirming evidence |
| Opportunity C | Evidence summary | Behaviour/root-cause questions | Disconfirming evidence |

The interviews must be allowed to confirm, refine, or reject the engine findings.

### 12.4 Do not select the final MVP yet

At this phase the valid output is:

> **Prioritized opportunity hypotheses for primary research.**

It is not:

> **Build Feature X.**

## Test Criteria

- multiple opportunities are visible
- rankings are explainable
- top findings have source evidence
- claims show denominators
- limitations are documented
- interview hypotheses include disconfirming conditions

## Exit Criteria

Phase 12 passes when the Discovery Engine has produced a defensible set of behavioural opportunities that can directly guide selection of interview participants and the required 5-6 primary interviews.

---

# 4. Phase Dependency Map

```text
Phase 0  Project bootstrap
   |
   v
Phase 1  Database + contracts
   |
   v
Phase 2  Source connectors
   |
   v
Phase 3  Deterministic preprocessing
   |
   v
Phase 4  AI schema + validation
   |
   v
Phase 5  End-to-end enrichment pipeline
   |
   v
Phase 6  Aggregation + segments + opportunities
   |
   v
Phase 7  API + hosting decision
   |
   +--------------------+
   |                    |
   v                    v
Phase 8 Dashboard    Phase 9 Human QA
   |                    |
   +---------+----------+
             |
             v
Phase 10 Real evaluator sample run
             |
             v
Phase 11 Production deployment / automation
             |
             v
Phase 12 Full corpus + research handoff
```

---

# 5. Critical Path vs Optional Enhancements

## Critical for the graduation project

The following must work before spending time on extras:

- multi-source evidence collection
- clean/deduplicate/relevance pipeline
- behaviour-first AI schema
- evidence spans
- transparent aggregation
- behavioural segment signals
- competing opportunity areas
- multi-factor ranking
- evidence drill-down
- deployed public dashboard
- real bounded evaluator sample run
- human validation of top findings

## Optional only after critical path is stable

- semantic clustering with embeddings
- `pgvector`
- sophisticated near-duplicate embeddings
- advanced animated dashboard components
- extensive admin console
- many additional source connectors
- complex user authentication
- real-time websocket streaming if polling is sufficient
- elaborate CI/CD
- GitHub Actions if simpler scheduling works
- Railway if serverless execution is sufficient

Do not delay the research output to build optional engineering features.

---

# 6. Recommended Build Order for AI Coding Agents

When using Antigravity or other coding agents, give each phase separately.

Do **not** prompt an agent to "build the entire engine" in one pass.

Recommended working loop:

1. Give the agent `problem statement.md`, `architecture.md`, and this implementation plan.
2. Tell it to implement **one phase only**.
3. Require tests for that phase.
4. Run the tests locally.
5. Review the diff.
6. Fix failures before moving forward.
7. Commit the completed phase.
8. Start the next phase in a fresh, explicit task.

For high-risk decisions such as:

- AI schema changes
- prompt interpretation rules
- opportunity-scoring logic
- source compliance
- segmentation logic
- deployment architecture changes

pause implementation and review the decision against the original problem statement before accepting the change.

---

# 7. Minimum Testing Matrix

| Layer | Minimum test |
|---|---|
| Connector | Real evidence returned + normalized + idempotent |
| Preprocessing | Cleaning + PII masking + duplicates |
| Relevance | Relevant vs irrelevant fixed examples |
| AI schema | Valid JSON/Pydantic contract |
| Evidence support | Returned span exists in source text |
| Aggregation | Counts and denominators correct |
| Ranking | Weights produce deterministic component + total scores |
| Opportunity mapping | Supports/contradicts/adjacent evidence retained |
| API | Correct typed payloads and filters |
| Dashboard | Findings change when database changes |
| Human review | Override preserved separately |
| Sample run | Real source -> real annotation -> real output |
| Deployment | Incognito evaluator smoke test |

---

# 8. Final Definition of Done

The Discovery Engine is ready to support the graduation project only when all of the following are true:

- [ ] public evidence is collected from multiple relevant sources
- [ ] raw source evidence is preserved
- [ ] evidence is cleaned, PII-masked, and duplicate-aware
- [ ] relevance filtering is working
- [ ] AI outputs a behaviour-first structured schema
- [ ] weak evidence can remain `unclear`
- [ ] important AI claims contain valid supporting source spans
- [ ] aggregation is deterministic
- [ ] every displayed percentage has a denominator
- [ ] behavioural segment signals are explainable
- [ ] multiple opportunity areas are generated
- [ ] opportunity scores are transparent and multi-factor
- [ ] contradictory evidence remains visible
- [ ] top evidence has been manually reviewed
- [ ] evaluator can inspect evidence behind findings
- [ ] evaluator can trigger a small real pipeline run
- [ ] dashboard is publicly deployed and testable
- [ ] no secrets are exposed
- [ ] findings are framed as hypotheses for primary research
- [ ] the engine has not selected the final MVP automatically

The next graduation-project step after this engine is:

**Discovery Engine findings -> target behavioural segment -> 5-6 primary interviews -> root cause -> final problem definition -> solution ideation -> final MVP**
