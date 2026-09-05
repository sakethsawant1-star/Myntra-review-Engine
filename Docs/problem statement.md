# Myntra Wishlist AI Discovery Engine - Problem Statement

## 1. Purpose of This Document

This document defines the problem that the **Myntra Wishlist AI Discovery Engine** must solve.

It is **not** the fellowship/project brief and it is **not** the final user problem statement for the graduation project. The original fellowship brief remains the source of truth for the overall project.

This document exists only to guide the design, architecture, implementation, testing, and deployment of the AI-powered review/discovery engine required in Part 1 of the project.

The engine must help us discover the underlying user problems that affect Myntra's wishlist-to-purchase conversion. It must not start with a predetermined answer or solution.

---

## 2. Business Context

Myntra users browse fashion products, save products they like, and add products to their wishlist. A wishlist is a strong expression of interest, but not every wishlisted item becomes a purchase.

The graduation project asks us, as a Product Manager on Myntra's Growth Team, to improve the following business metric:

> **Increase the percentage of users who purchase at least one item from their wishlist within 30 days of adding it.**

For this project, the primary business metric is defined as:

> **30-Day Wishlist-to-Purchase Conversion Rate = Number of users who purchase at least one item they wishlisted within 30 days / Number of users who added at least one item to their wishlist**

The engine's role is not to directly improve this metric. Its role is to identify and compare the user behaviours, uncertainties, frictions, and unmet needs that may be preventing the metric from improving.

---

## 3. Core Discovery Problem

We currently do **not** know why a meaningful share of Myntra wishlist activity does not convert into purchase within 30 days.

A wishlist can represent many different behaviours. For example, a user may be expressing genuine purchase intent, saving an item for later, comparing alternatives, collecting inspiration, waiting for more information, or simply bookmarking something they like.

We must therefore avoid assuming that every wishlist addition represents the same intent or that one specific factor - such as price, size, fit, reviews, or styling - is the dominant problem.

The engine must analyze public user conversations at scale and help us answer:

1. Why do users save fashion products to wishlists?
2. When does a wishlist represent genuine purchase intent versus passive bookmarking?
3. What prevents users with purchase intent from completing a purchase?
4. What uncertainties remain after a user has already identified an item they like?
5. What causes users to postpone the decision rather than buy immediately?
6. What happens after wishlisting and before either purchase or abandonment?
7. How do users compare multiple shortlisted products?
8. What information do users seek outside Myntra before deciding?
9. What workarounds do users use when the platform does not resolve their uncertainty?
10. How do these behaviours vary across identifiable behavioural segments?
11. Which recurring unmet needs appear most likely to influence 30-day wishlist-to-purchase conversion?

---

## 4. Objective of the Discovery Engine

Build a **deployed, testable AI-powered discovery system** that collects and analyzes publicly available user conversations about Myntra and online fashion-shopping behaviour, then converts those conversations into structured, evidence-backed product insights.

The engine must enable us to move from:

**Raw public conversation -> Relevant evidence -> Behavioural interpretation -> User friction / uncertainty -> Segment signal -> Opportunity area -> Prioritized research hypothesis**

The engine is successful only if its output helps us decide **what deserves deeper primary research**. It must not simply summarize reviews or produce sentiment scores.

---

## 5. Scope of Evidence

The engine should work with publicly available conversations relevant to Myntra and online fashion shopping.

Potential sources include:

- Google Play Store reviews for Myntra
- Apple App Store reviews for Myntra
- Reddit discussions
- Public fashion/shopping communities and forums
- Public social-media conversations where technically and legally accessible
- YouTube comments on Myntra/fashion-shopping content
- Product reviews and Q&A where relevant and publicly accessible
- Other public conversations that reveal pre-purchase, wishlist, comparison, fit, styling, trust, or decision behaviour

The architecture should allow additional sources to be added later without rebuilding the analysis layer.

### Source principle

The engine should prioritize **decision-useful evidence**, not raw volume alone. A long-form discussion that explains what a user did after wishlisting may be more valuable than a one-line rating complaint.

---

## 6. Required Analysis Depth

The fellowship brief explicitly requires the engine to go beyond summarization and sentiment analysis.

Therefore, each relevant piece of user feedback should be analyzed for as many of the following fields as the evidence actually supports.

### 6.1 Core evidence fields

- Source
- Date / recency where available
- Raw text
- Cleaned text
- Relevance to wishlist / purchase-decision behaviour
- Evidence confidence
- Representative quote / evidence excerpt

### 6.2 Behavioural fields

- Reason for saving / shortlisting
- Likely wishlist intent
  - Genuine purchase consideration
  - Comparison / shortlist
  - Buy-later intent
  - Inspiration / bookmarking
  - Unclear
- Current purchase-decision stage
- Behaviour after saving
- Revisit behaviour
- Comparison behaviour
- Off-platform information seeking
- Workaround used
- Purchase trigger, if stated
- Abandonment / loss-of-interest signal, if stated

### 6.3 Friction and uncertainty fields

The model may classify evidence into areas such as the following **only when supported by the source text**:

- Fit uncertainty
- Size uncertainty
- Styling / coordination uncertainty
- Product-quality uncertainty
- Review / trust uncertainty
- Product-information gap
- Occasion suitability
- Social validation
- Comparison difficulty
- Availability / stock concern
- Delivery / timing concern
- Price-related behaviour
- Return / exchange concern
- Choice overload
- Forgetting / low salience
- Other emerging friction

These categories are an initial taxonomy for analysis, **not predetermined conclusions**. The engine must allow new themes to emerge from the data.

### 6.4 Severity and conversion relevance

Where evidence permits, the engine should estimate:

- Severity of friction
- Whether the friction appears to delay purchase, prevent purchase, or merely create inconvenience
- Strength of stated purchase intent
- Proximity to purchase
- Whether the behaviour is plausibly related to conversion within the 30-day window

---

## 7. Behavioural Segmentation Requirement

The engine should help identify behavioural segments rather than relying primarily on demographics.

Possible segmentation dimensions may emerge around:

- Strength of purchase intent
- Level/type of uncertainty
- Frequency of wishlist usage
- Active comparison versus passive saving
- Reliance on off-platform research
- Revisit behaviour
- Decision urgency
- Purchase versus abandonment patterns

No final target segment should be hard-coded into the engine before analysis.

The output should allow us to compare segments and determine which one is most relevant for deeper primary research.

---

## 8. Opportunity Identification and Ranking

The engine should convert patterns into **opportunity areas**, not feature ideas.

An opportunity should describe a user need, friction, uncertainty, or broken behaviour that may influence wishlist-to-purchase conversion.

Example structure:

> Users with [behaviour / intent] struggle to [complete desired behaviour] because [observed uncertainty or friction], causing [delay / comparison / abandonment / workaround].

The engine should rank or compare opportunity areas using evidence such as:

- Frequency - how often the pattern appears
- Severity - how strongly it affects the user decision
- Purchase-intent strength - whether affected users appear close to purchase
- Conversion relevance - likelihood that resolving the issue could influence 30-day wishlist conversion
- Source convergence - whether the same pattern appears across multiple independent sources
- Segment concentration - whether the issue is especially strong for a specific behavioural segment
- Evidence confidence - how directly the source text supports the interpretation

The ranking method must be transparent enough to explain in the final deck.

The engine must **not** rank an issue solely because it has the highest number of mentions.

---

## 9. Required Outputs

The engine should provide a dashboard or testable interface that allows the evaluator/product team to inspect the analysis.

At minimum, the output should show:

1. Number of raw conversations collected
2. Number retained after cleaning/relevance filtering
3. Source distribution
4. Major behavioural patterns
5. Reasons for wishlisting where identifiable
6. Purchase-intent patterns
7. Major unresolved uncertainties / blockers
8. Behaviour after wishlisting
9. Off-platform research and workarounds
10. Behavioural segment signals
11. Ranked opportunity areas
12. Evidence supporting each opportunity
13. Representative user quotes with PII removed
14. Confidence / evidence strength
15. Ability to inspect the underlying evidence behind a finding

Where useful, the dashboard may also provide filters for:

- Source
- Date
- Theme / friction
- Intent type
- Behavioural segment
- Purchase stage
- Sentiment
- Severity
- Confidence

---

## 10. Human-in-the-Loop Requirement

The engine is a discovery aid, not an autonomous product-decision maker.

AI-generated classifications and opportunity scores must remain inspectable against the original user evidence.

We must be able to:

- Open representative raw evidence behind a finding
- Identify obvious misclassifications
- Re-run or refine analysis rules/prompts
- Distinguish strong evidence from inference
- Preserve contradictory evidence rather than hiding it

The engine's findings will later be validated, refined, or challenged through the required 5-6 primary user interviews.

---

## 11. Data Quality Requirements

Before analysis, the pipeline should perform appropriate processing such as:

- Text normalization
- Duplicate / near-duplicate removal
- Spam and irrelevant-content filtering
- Language handling where required
- PII removal or masking
- Source metadata preservation
- Relevance scoring

The pipeline should preserve raw source text separately from cleaned/AI-enriched fields so that results remain auditable.

---

## 12. AI Requirements

AI should be used where semantic interpretation is necessary, including tasks such as:

- Relevance classification
- Behaviour extraction
- Intent interpretation
- Theme discovery / classification
- Friction and uncertainty detection
- Workaround extraction
- Segment-signal extraction
- Evidence summarization
- Opportunity synthesis

However:

- Deterministic logic should be used for calculations, counts, filtering rules, deduplication, and ranking arithmetic where appropriate.
- AI must not fabricate user intent that is unsupported by the source text.
- Low-confidence or ambiguous cases should be marked as unclear instead of forced into a category.
- Representative quotes must come from actual collected evidence, not be generated by the model.

---

## 13. Non-Goals

The Discovery Engine is **not** intended to:

- Decide the final MVP before research is complete
- Prove that any specific factor such as price, fit, size, styling, or reviews is already the root cause
- Generate a solution simply because a theme appears frequently
- Replace the required 5-6 primary interviews
- Predict Myntra's private internal conversion rate without access to internal data
- Claim causal impact from public reviews alone
- Offer monetary incentives as a proposed solution
- Function merely as a sentiment-analysis dashboard

---

## 14. Functional Success Criteria

The first production-ready version of the engine should satisfy the following:

- Collect public user evidence from multiple relevant sources
- Clean, deduplicate, and filter the evidence
- Use AI to transform unstructured text into the defined behavioural schema
- Produce repeatable aggregate analysis
- Identify multiple competing opportunity areas
- Compare those opportunities using more than mention volume alone
- Surface behavioural segment signals
- Preserve direct evidence behind every important finding
- Support human review of AI classifications
- Be accessible through a deployed, testable link
- Allow an evaluator to understand how raw user feedback becomes a ranked product insight

---

## 15. Product Decision Output

The final output of this engine should not be:

> "Build Feature X."

It should instead give us an evidence-backed set of statements such as:

> "Opportunity A appears frequently among users with strong purchase intent, is associated with repeated comparison and off-platform workarounds, and has stronger evidence of delaying purchase than Opportunity B. This should be tested in primary interviews."

That output will feed directly into the next stages of the graduation project:

**Business Metric -> AI Discovery -> Opportunity Comparison -> Target Segment -> Primary Research -> Root Cause -> Problem Definition -> Solution Ideation -> MVP**

---

## 16. Guiding Principles

1. **Discover before solving.** Do not encode the desired answer into the prompts or taxonomy.
2. **Behaviour over sentiment.** What users do before and after wishlisting matters more than whether a review is simply positive or negative.
3. **Evidence over AI confidence.** Every important insight should be traceable to real user conversations.
4. **Segment by behaviour.** Avoid premature demographic personas.
5. **Compare opportunities.** The most-mentioned issue is not automatically the best product opportunity.
6. **Stay tied to the business metric.** Every shortlisted opportunity must have a plausible relationship to 30-day wishlist-to-purchase conversion.
7. **Do not overclaim causality.** Public conversation generates hypotheses; primary research validates and deepens them.
8. **Keep the engine extensible.** Sources, taxonomies, prompts, and ranking logic should be replaceable or configurable as findings evolve.

---

## 17. Definition of Done for This Problem Statement

This specification is complete when it is sufficiently clear to design the next project documents without deciding the research outcome in advance.

The next documents to create from this specification are:

1. `architecture.md` - system components, data flow, storage, AI layer, APIs, dashboard, deployment approach
2. `implementation plan.md` - phased build plan with test criteria for each phase
3. Analysis schema / taxonomy configuration
4. Source acquisition plan
5. Validation and QA plan

