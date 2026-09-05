# AG_CONTEXT.md - Antigravity Project Handoff

## 1. Purpose

This file is the persistent context/handoff document for any Antigravity agent, Gemini model, Claude model, or coding assistant working on this repository.

**Read this file first at the beginning of every new session.** Then read the referenced project documents in the order specified below before changing code or architecture.

The goal is to preserve continuity and prevent different agents from independently reinterpreting the project.

---

## 2. Project Identity

**Project:** NextLeap Graduation Project - Myntra

**Role assumed in fellowship brief:** Product Manager on Myntra's Growth Team

**Primary business goal:** Increase the percentage of users who purchase at least one item from their Myntra wishlist within 30 days of adding an item.

**Primary metric:**

> **30-Day Wishlist-to-Purchase Conversion Rate = Number of users who purchase at least one item they wishlisted within 30 days / Number of users who added at least one item to their wishlist**

The project must not use monetary incentives as the final solution.

---

## 3. Critical Distinction Between Problem Statements

There are two different concepts called "problem statement" in this project. Do not confuse them.

### A. Original fellowship/project brief

The original NextLeap problem statement and guidelines supplied by the fellow are the **source of truth for the overall graduation-project requirements, constraints, deliverables, research expectations, Discovery Engine requirement, MVP requirement, and final submission rules**.

It is broader than this repository's engine specification.

### B. `problem statement.md` in this repository

`problem statement.md` is **NOT the original fellowship brief**.

It is an internal specification created specifically to guide the design and construction of the **Myntra Wishlist AI Discovery Engine / Review Engine**.

It defines what the engine must discover, what evidence it should collect, what behavioural fields it should extract, how opportunities should be identified, and what the engine must not assume.

Do not reinterpret `problem statement.md` as the final user problem. The final user problem is intentionally unknown until discovery + primary research are completed.

---

## 4. Read These Files in This Order

Before implementation or major technical decisions, read:

1. **This file - `AG_CONTEXT.md`**
2. **Original NextLeap fellowship/project brief** if it has been supplied to the working environment
3. **`problem statement.md`** - Discovery Engine specification
4. **`architecture.md`** - approved technical architecture
5. **`implementation plan.md`** - approved phase-wise build plan

Treat these documents as the current source of truth.

If two documents appear to conflict:

1. Original fellowship brief wins for fellowship requirements.
2. `problem statement.md` wins for Discovery Engine product/research intent.
3. `architecture.md` wins for current technical boundaries.
4. `implementation plan.md` wins for execution order unless a technical blocker is demonstrated.

Do not silently resolve a conflict by inventing a new requirement. Flag it first.

---

## 5. Current Project Stage

### Completed planning work

- Myntra selected as the platform.
- Primary metric defined.
- Low-effort research screener designed.
- Screener recruitment window set to **30-45 days** to widen participant availability while keeping the business metric itself at 30 days.
- Discovery Engine `problem statement.md` completed.
- Discovery Engine `architecture.md` completed.
- Phase-wise `implementation plan.md` completed.

### Primary research status

A short participant screener is intended to be circulated while the Discovery Engine is being built.

Target workflow:

- Collect approximately **25-40 screener responses** where practical.
- Shortlist approximately **8-10 relevant candidates**.
- Conduct **5-6 actual interviews**.
- Interviews can be approximately **8-10 minutes**; they do not need to be 20-minute formal sessions.
- Interviews should discuss real/recent wishlist behaviour and, where possible, real wishlisted items.

**Do not use survey/interview assumptions to hard-code a problem into the engine.**

### Engineering status

**No Discovery Engine implementation should be assumed complete yet.**

The next engineering action is to begin **Phase 0 - Project Bootstrap and Guardrails** from `implementation plan.md`, then proceed sequentially.

---

## 6. Core Research Rule - Do Not Predetermine the Problem

The engine exists to discover why wishlist activity does not convert to purchase within 30 days.

Do **NOT** assume in advance that the main problem is:

- price
- discounts
- fit
- size
- styling
- reviews
- product quality
- trust
- delivery
- comparison
- choice overload
- social validation
- AI assistance
- reminders
- any other feature or friction

These are candidate signals/taxonomy labels only when evidence supports them.

The correct flow is:

**Business Metric -> Public Evidence -> Behavioural Analysis -> Opportunity Comparison -> Behavioural Segment -> Primary Research -> Root Cause -> Solution Ideation -> MVP**

Do not reverse this flow.

---

## 7. What the Discovery Engine Must Do

The engine must be a **real, deployed, testable AI-powered discovery system**, not a static dashboard or a manually prepared research summary.

The intended evidence chain is:

**Raw public conversation -> Cleaned evidence -> Structured behavioural interpretation -> User friction/uncertainty -> Segment signal -> Opportunity area -> Prioritized primary-research hypothesis**

It must go beyond sentiment and generic theme counting.

Where supported by evidence, analysis should capture fields such as:

- source and source metadata
- raw text and cleaned text
- relevance
- reason for saving/shortlisting
- likely wishlist intent
- purchase-decision stage
- behaviour after saving
- revisit behaviour
- comparison behaviour
- off-platform research
- workaround used
- unresolved uncertainty/friction
- purchase trigger
- abandonment signal
- strength of purchase intent
- severity
- likely conversion relevance
- behavioural segment signal
- evidence confidence
- representative evidence/quote

No model should fabricate unsupported intent or causes.

---

## 8. Opportunity Ranking Rule

The previous Spotify project over-relied on mention volume. Do not repeat that.

An opportunity must not rank #1 only because it has the most mentions.

Opportunity comparison should consider multiple evidence dimensions defined in the architecture, including where available:

- frequency
- severity
- purchase-intent strength
- proximity to purchase
- conversion relevance
- source convergence
- segment concentration
- evidence confidence

The scoring method must remain explainable enough to show in the final fellowship deck.

All important percentages must expose their denominator.

---

## 9. Technology Direction

### Default lean stack

Use the simplest stack that satisfies the architecture:

- **Supabase** - PostgreSQL/database, storage where useful, and lightweight server-side functionality
- **Vercel** - frontend/dashboard deployment
- **AI provider abstraction** - Gemini or another approved model for semantic interpretation

### Railway

Railway is **not mandatory by default**.

Add Railway + FastAPI only if real implementation proves it is needed, for example:

- scraping exceeds serverless runtime limits
- long-running AI/batch jobs need workers
- Python dependency/runtime constraints make serverless unsuitable
- evaluator-triggered sample runs cannot execute reliably without a persistent backend

### GitHub Actions

GitHub Actions is **optional**.

Add it only if scheduled/full-corpus pipeline runs need an external job runner and Supabase/Vercel scheduling is insufficient.

Do not add infrastructure merely because it existed in the Spotify project.

---

## 10. AI / Model Usage Strategy

The working environment may have access to multiple models.

Recommended division of labour:

### Routine implementation

Use a fast/cost-efficient model for:

- boilerplate
- standard UI components
- straightforward database CRUD
- simple tests
- repetitive refactors
- documentation updates

### Complex engineering/reasoning

Use a stronger reasoning/coding model for:

- architecture-impacting decisions
- difficult scraper/integration bugs
- schema changes with downstream consequences
- AI evaluation failures
- opportunity-scoring design
- security/reliability issues
- difficult debugging

### Adversarial review

A separate strong model may be used as a critic at major checkpoints, but it should **challenge the existing plan rather than independently redesign the whole project**.

Any proposed architecture or product-reasoning change must be reconciled with the source-of-truth documents before implementation.

---

## 11. Engineering Rules

1. Follow `implementation plan.md` phase by phase.
2. Do not skip phase exit criteria merely to make visible progress faster.
3. Build the evidence chain before polishing the dashboard.
4. Keep raw source evidence immutable.
5. Keep cleaned/masked text separate from raw text.
6. Version AI annotations/prompts/configuration where specified.
7. Keep human review/override separate from original AI output.
8. Preserve contradictory evidence.
9. Make imports/runs idempotent where designed.
10. Never commit `.env` files, credentials, API keys, service-role keys, database passwords, tokens, or secrets.
11. Use `.env.example` with variable names only.
12. Do not bypass CAPTCHAs, paywalls, anti-bot controls, authentication, or source restrictions.
13. If a source is technically or legally unsuitable, replace/remove the source rather than circumventing protections.
14. Prefer deterministic processing for deterministic tasks and AI for semantic interpretation.
15. Every important AI conclusion must remain traceable back to source evidence.

---

## 12. Evaluator/Testability Requirement

The Discovery Engine should ultimately have a public/testable interface.

If the dashboard provides a **Run / Analyze / Refresh** action, it must trigger a **real bounded pipeline execution** or clearly labelled real sample run.

Do **not** create a fake progress animation that merely writes staged logs while no analysis occurs.

For evaluator safety/cost control, the public run may be intentionally bounded by:

- number of sources
- records per source
- time window
- AI batch size
- execution timeout

A larger preprocessed corpus may coexist with this sample-run capability.

---

## 13. Final Customer MVP Boundary

The Discovery Engine and the final graduation-project MVP are two different deliverables.

Do **not** start building the final customer-facing MVP merely because an interesting feature idea appears during scraping.

The final MVP should only begin after:

1. Discovery Engine findings exist.
2. Opportunity areas have been compared.
3. A behavioural target segment has been selected using evidence.
4. 5-6 primary interviews have been conducted.
5. Discovery findings have been confirmed/refined/challenged.
6. A defensible root cause has been established.
7. Multiple materially different solution approaches have been considered.

AI does not automatically need to be part of the customer-facing MVP. It should be used only if it genuinely earns its place.

---

## 14. Lessons From the Previous Spotify Project

The previous project demonstrated strong technical execution but had gaps between evidence, root cause, solution, and metrics.

Do not repeat these mistakes:

- Do not turn a broad theme into a narrow root cause without evidence.
- Do not combine different research findings into a stronger headline than the data supports.
- Do not treat total platform population as the target opportunity size.
- Do not let the intended solution determine the target segment.
- Do not define the root cause as "Feature X does not exist" or "Feature X is paywalled."
- Do not let all solution alternatives belong to essentially the same solution family.
- Do not use arbitrary metric-improvement targets without a baseline/rationale.
- Do not spend disproportionate final-deck space on engineering architecture at the expense of PM reasoning.

The standard for this project is:

> **Prove that the thing eventually built is the thing the evidence earned the right to build.**

---

## 15. Change-Control Protocol

Do not silently rewrite the core planning documents.

If implementation reveals that `architecture.md` or `implementation plan.md` should change:

1. State the blocker or evidence.
2. Identify the affected section(s).
3. Explain the proposed change and its downstream impact.
4. Preserve the research-neutral intent of `problem statement.md`.
5. Get approval before making a material architecture/product-direction change, unless the change is a minor implementation detail that does not alter system boundaries.

When a change is approved, update the relevant markdown file so future agents inherit the new decision.

---

## 16. Session Continuity Protocol

At the end of each meaningful build session, update the **Project Status** section below with:

- current phase
- completed tasks
- tests run and results
- open bugs/blockers
- architecture deviations approved
- next exact action

Do not rely only on chat history for project continuity.

---

## 17. Project Status

**Current phase:** Phase 0 - Project Bootstrap and Guardrails

**Implementation status:** Not started / ready to begin

**Research status:** Screener prepared; distribution/responses handled in parallel with engine implementation

**Approved default deployment:** Supabase + Vercel first

**Railway:** Optional; decision deferred until real runtime constraints are observed

**GitHub Actions:** Optional; add only if scheduling/job execution requires it

**Final MVP:** Not started and must not be started yet

### Next exact action

Read `problem statement.md`, `architecture.md`, and `implementation plan.md` completely, then execute **Phase 0** exactly as defined in `implementation plan.md`.

Before proceeding to Phase 1, verify and report the Phase 0 test criteria and exit criteria.

---

## 18. Suggested First Prompt for a New Antigravity Session

> Read `AG_CONTEXT.md` first, then read `problem statement.md`, `architecture.md`, and `implementation plan.md` completely. Treat them as the source of truth. We are currently at Phase 0 of the Discovery Engine implementation. Execute only Phase 0, run its required tests/checks, report what changed and whether the exit criteria passed. Do not change product assumptions or architecture without first explaining the reason.

