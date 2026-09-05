"""
AI Annotation Schema — Expanded for full problem-statement coverage.

Rules:
- Never fabricate intent. Use 'unclear' or 'not_applicable' if the text lacks proof.
- Multiple behaviours, reasons, and frictions may coexist.
- Exact supporting spans must be present for important claims.
- 'other' and 'emerging_theme' are valid outputs — the taxonomy must not decide the winner.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ─── Friction / Uncertainty Span ─────────────────────────────

class FrictionSpan(BaseModel):
    """Specific friction or uncertainty mentioned in the text."""
    type: Literal[
        "fit_uncertainty",
        "size_uncertainty",
        "styling_coordination_uncertainty",
        "product_quality_uncertainty",
        "review_trust_uncertainty",
        "product_information_gap",
        "occasion_suitability",
        "social_validation",
        "comparison_difficulty",
        "availability_stock_concern",
        "delivery_timing_concern",
        "price_related_behaviour",
        "return_exchange_concern",
        "choice_overload",
        "forgetting_low_salience",
        "platform_usability_issue",
        "other_emerging_friction",
        "unclear",
    ] = Field(description="The category of friction or uncertainty.")
    label: str = Field(description="Short 1-3 word label of the specific friction.")
    severity: int = Field(description="1=Low (annoyance), 2=Medium (hesitation), 3=High (blocker). Integer between 1 and 3.")
    support_span: str = Field(description="Exact quote from the text that proves this friction.")


# ─── Support Span ────────────────────────────────────────────

class SupportSpan(BaseModel):
    """Generic evidence span to support a claim."""
    claim: str = Field(description="The claim being supported.")
    exact_quote: str = Field(description="The exact substring from the source text proving this claim.")


# ─── Reason for Saving ───────────────────────────────────────

ReasonForSaving = Literal[
    "genuine_purchase_consideration",
    "compare_alternatives",
    "buy_later",
    "price_monitoring",
    "future_event_or_occasion",
    "inspiration_or_bookmarking",
    "availability_monitoring",
    "unclear",
    "other",
]

# ─── Wishlist Intent ──────────────────────────────────────────

WishlistIntent = Literal[
    "high_purchase_intent",
    "active_comparison",
    "delayed_purchase_intent",
    "passive_bookmarking",
    "price_monitoring",
    "unclear",
    "not_applicable",
]

# ─── Purchase Stage ───────────────────────────────────────────

PurchaseStage = Literal[
    "browsing",
    "shortlisted",
    "evaluating_alternatives",
    "resolving_uncertainty",
    "ready_to_buy",
    "delayed",
    "abandoned",
    "purchased",
    "unclear",
]

# ─── Post-Save Behaviours ────────────────────────────────────

PostSaveBehaviour = Literal[
    "revisited_item",
    "compared_within_myntra",
    "compared_across_platforms",
    "checked_reviews",
    "searched_google",
    "searched_youtube",
    "checked_social_content",
    "asked_another_person",
    "added_to_bag",
    "waited",
    "forgot",
    "bought_elsewhere",
    "bought_another_item",
    "no_action_stated",
    "unclear",
    "other",
]

# ─── Workaround ──────────────────────────────────────────────

Workaround = Literal[
    "bought_elsewhere",
    "bought_different_item",
    "asked_customer_care",
    "searched_video_social",
    "asked_another_person",
    "waited_for_price_stock",
    "returned_later",
    "none",
    "unclear",
    "other",
]

# ─── Purchase Trigger ────────────────────────────────────────

PurchaseTrigger = Literal[
    "price_drop",
    "sale_event",
    "urgency",
    "positive_review",
    "restock",
    "social_recommendation",
    "none",
    "unclear",
    "other",
]

# ─── Abandonment Signal ──────────────────────────────────────

AbandonmentSignal = Literal[
    "bought_competitor",
    "lost_interest",
    "price_too_high",
    "fit_fear",
    "quality_concern",
    "found_better_alternative",
    "item_unavailable",
    "none",
    "unclear",
    "other",
]

# ─── Off-Platform Research Channel ────────────────────────────

OffPlatformChannel = Literal[
    "youtube",
    "reddit",
    "instagram",
    "google_search",
    "other_shopping_platform",
    "in_store",
    "friends_family",
    "fashion_blog",
    "unclear",
    "not_applicable",
]


# ═════════════════════════════════════════════════════════════
# Main AIAnnotation Schema
# ═════════════════════════════════════════════════════════════

class AIAnnotation(BaseModel):
    """
    Strict schema for AI behavioural extraction from a Myntra review or comment.

    Rules:
    - Never fabricate intent. Use 'unclear' or 'not_applicable' when evidence is weak.
    - Multiple values are allowed for list fields.
    - Do not guess demographics, solutions, or features.
    - Extract exact substrings as support spans.
    """

    # ── Relevance ─────────────────────────────────────
    wishlist_relevance: Literal["high", "medium", "low", "unclear", "not_applicable"] = Field(
        description="How relevant is this text to understanding wishlist or pre-purchase behavior?"
    )

    # ── Why they saved ────────────────────────────────
    reason_for_saving: List[ReasonForSaving] = Field(
        description="Why did the user save / wishlist this item? May have multiple reasons."
    )

    # ── Intent ────────────────────────────────────────
    wishlist_intent: WishlistIntent = Field(
        description="The user's underlying intent behind wishlisting."
    )
    intent_strength: int = Field(
        description="0=None, 1=Low (bookmark), 2=Medium (considering), 3=High (ready to buy). Integer between 0 and 3."
    )

    # ── Decision stage ────────────────────────────────
    purchase_stage: PurchaseStage = Field(
        description="Where the user is in their purchase decision journey."
    )
    proximity_to_purchase: Literal["far", "near", "completed", "abandoned", "unclear"] = Field(
        description="How close the user is to actually purchasing."
    )

    # ── Post-save behaviour ───────────────────────────
    behaviour_after_saving: List[PostSaveBehaviour] = Field(
        description="What did the user do after saving/wishlisting? Multiple behaviours allowed."
    )
    revisit_behaviour: Literal[
        "frequent_checking", "infrequent", "never_revisited", "unclear", "not_applicable"
    ] = Field(description="How often the user revisits the wishlisted item.")

    # ── Comparison & research ─────────────────────────
    comparison_behaviour: Literal[
        "compared_on_myntra", "compared_cross_platform", "no_comparison", "unclear", "not_applicable"
    ] = Field(description="How the user compares products.")
    off_platform_research: List[OffPlatformChannel] = Field(
        description="Where did the user go for off-platform research?"
    )
    information_sought: List[str] = Field(
        description="What specific information was the user looking for? Brief phrases."
    )

    # ── Workarounds ───────────────────────────────────
    workaround: List[Workaround] = Field(
        description="What workarounds did the user employ when Myntra didn't resolve uncertainty?"
    )

    # ── Triggers & signals ────────────────────────────
    purchase_trigger: List[PurchaseTrigger] = Field(
        description="What triggered the user to finally purchase, if stated."
    )
    abandonment_signal: List[AbandonmentSignal] = Field(
        description="What signals indicate the user abandoned the wishlist item?"
    )

    # ── Frictions ─────────────────────────────────────
    frictions: List[FrictionSpan] = Field(
        description="Any uncertainties or blockers mentioned."
    )

    # ── Emerging themes ───────────────────────────────
    emerging_themes: List[str] = Field(
        description="Any interesting new behavioural themes not covered by the taxonomy. 2-4 words each."
    )

    # ── Scoring fields ────────────────────────────────
    conversion_relevance: int = Field(
        description="How relevant is this specifically to wishlist-to-purchase conversion? 0=none, 3=high. Integer between 0 and 3."
    )
    evidence_confidence: int = Field(
        description="1=Low (inferred), 2=Medium (stated vaguely), 3=High (stated explicitly). Integer between 1 and 3."
    )

    # ── Segment signals ───────────────────────────────
    segment_signals: List[str] = Field(
        description="e.g. 'price_sensitive', 'fit_anxious', 'brand_loyal'. Brief labels."
    )

    # ── Evidence spans ────────────────────────────────
    supporting_spans: List[SupportSpan] = Field(
        description="Crucial exact quotes from the source text supporting the main findings."
    )
    contradictory_signal: Optional[str] = Field(
        description="Any evidence in the text that contradicts the main interpretation. Null if none."
    )

    # ── Notes ─────────────────────────────────────────
    analysis_notes: Optional[str] = Field(
        description="Genuine analyst/model notes about edge cases or ambiguity. NOT for storing structured data."
    )

# ═════════════════════════════════════════════════════════════
# Batch Wrapper Schema
# ═════════════════════════════════════════════════════════════

class AIBatchResponse(BaseModel):
    """
    Wrapper schema for processing multiple reviews in a single AI request.
    The length of the annotations array MUST match the number of reviews provided.
    """
    annotations: List[AIAnnotation] = Field(
        description="List of annotations, one for each input review in exactly the same order."
    )

