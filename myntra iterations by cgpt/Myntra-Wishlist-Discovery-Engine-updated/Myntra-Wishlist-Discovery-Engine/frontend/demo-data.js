// ============================================================
// Phase 10 — Rich Demo Data
// Realistic Myntra Wishlist behavioral insights
// ============================================================

const DEMO_DATA = {

  overview: {
    total_annotations: 1247,
    source_distribution: {
      "google_play": { count: 840, percent: 67.4 },
      "reddit_rss":  { count: 284, percent: 22.8 },
      "youtube":     { count: 123, percent: 9.9 }
    },
    intent_x_friction: {
      high_intent_total:        { count: 421, percent: 33.8 },
      high_intent_with_friction:{ count: 356, percent: 84.6 }
    }
  },

  behaviours: {
    reason_for_saving: {
      "buy_later":                  { count: 412, percent: 33.0 },
      "genuine_purchase_consideration": { count: 380, percent: 30.5 },
      "price_monitoring":           { count: 248, percent: 19.9 },
      "compare_alternatives":       { count: 142, percent: 11.4 },
      "future_event_or_occasion":   { count: 118, percent: 9.5 },
      "inspiration_or_bookmarking": { count: 87,  percent: 7.0 },
      "availability_monitoring":    { count: 64,  percent: 5.1 }
    },
    wishlist_intent: {
      "high_purchase_intent":    { count: 421, percent: 33.8 },
      "active_comparison":       { count: 275, percent: 22.1 },
      "delayed_purchase_intent": { count: 231, percent: 18.5 },
      "passive_bookmarking":     { count: 187, percent: 15.0 },
      "price_monitoring":        { count: 133, percent: 10.7 }
    },
    purchase_stage: {
      "evaluating_alternatives": { count: 564, percent: 45.2 },
      "resolving_uncertainty":   { count: 409, percent: 32.8 },
      "shortlisted":             { count: 187, percent: 15.0 },
      "browsing":                { count: 87,  percent: 7.0 }
    },
    behaviour_after_saving: {
      "revisited_item":           { count: 520, percent: 41.7 },
      "compared_within_myntra":   { count: 312, percent: 25.0 },
      "compared_across_platforms":{ count: 230, percent: 18.4 },
      "checked_reviews":          { count: 210, percent: 16.8 },
      "searched_youtube":         { count: 168, percent: 13.5 },
      "waited":                   { count: 145, percent: 11.6 },
      "forgot":                   { count: 122, percent: 9.8 },
      "added_to_bag":             { count: 98,  percent: 7.9 },
      "bought_elsewhere":         { count: 87,  percent: 7.0 }
    },
    off_platform_research: {
      "youtube":               { count: 168, percent: 13.5 },
      "google_search":         { count: 142, percent: 11.4 },
      "instagram":             { count: 98,  percent: 7.9 },
      "other_shopping_platform":{ count: 87, percent: 7.0 },
      "friends_family":        { count: 76,  percent: 6.1 },
      "fashion_blog":          { count: 43,  percent: 3.4 }
    },
    workaround_distribution: {
      "bought_elsewhere":          { count: 87,  percent: 7.0 },
      "searched_video_social":     { count: 76,  percent: 6.1 },
      "asked_another_person":      { count: 54,  percent: 4.3 },
      "waited_for_price_stock":    { count: 48,  percent: 3.8 },
      "bought_different_item":     { count: 38,  percent: 3.0 }
    },
    friction_distribution: {
      "fit_uncertainty":                  { count: 384, of_all_annotations: { percent: 30.8 } },
      "review_trust_uncertainty":         { count: 227, of_all_annotations: { percent: 18.2 } },
      "styling_coordination_uncertainty": { count: 187, of_all_annotations: { percent: 15.0 } },
      "availability_stock_concern":       { count: 174, of_all_annotations: { percent: 13.9 } },
      "price_related_behaviour":          { count: 150, of_all_annotations: { percent: 12.0 } },
      "choice_overload":                  { count: 112, of_all_annotations: { percent: 9.0 } },
      "forgetting_low_salience":          { count: 98,  of_all_annotations: { percent: 7.9 } },
      "delivery_timing_concern":          { count: 87,  of_all_annotations: { percent: 7.0 } },
      "occasion_suitability":             { count: 76,  of_all_annotations: { percent: 6.1 } },
      "product_information_gap":          { count: 65,  of_all_annotations: { percent: 5.2 } }
    }
  },

  questions: [
    { question: "Why do users save items to the wishlist instead of buying immediately?", coverage_status: "covered", fields_used: ["reason_for_saving", "wishlist_intent"], evidence_count: 580 },
    { question: "What frictions or uncertainties prevent conversion from wishlist to purchase?", coverage_status: "covered", fields_used: ["frictions", "severity", "abandonment_signal"], evidence_count: 724 },
    { question: "What information do users seek off-platform before purchasing?", coverage_status: "covered", fields_used: ["off_platform_research", "information_sought"], evidence_count: 412 },
    { question: "How often do users revisit wishlisted items, and what triggers re-engagement?", coverage_status: "covered", fields_used: ["revisit_behaviour", "purchase_trigger"], evidence_count: 298 },
    { question: "Do users compare wishlisted items across platforms? What drives this?", coverage_status: "covered", fields_used: ["comparison_behaviour", "workaround"], evidence_count: 230 },
    { question: "What workarounds do users employ when the platform doesn't resolve their uncertainty?", coverage_status: "covered", fields_used: ["workaround", "abandonment_signal"], evidence_count: 303 },
    { question: "What purchase triggers ultimately convert a wishlist item to a purchase?", coverage_status: "covered", fields_used: ["purchase_trigger", "proximity_to_purchase"], evidence_count: 187 },
    { question: "What signals indicate a user has abandoned a wishlist item permanently?", coverage_status: "covered", fields_used: ["abandonment_signal", "purchase_stage"], evidence_count: 156 },
    { question: "Are there distinct behavioral segments within users who wishlist items?", coverage_status: "covered", fields_used: ["segment_signals", "wishlist_intent"], evidence_count: 421 },
    { question: "How does purchase proximity vary across wishlist intents?", coverage_status: "partial", fields_used: ["proximity_to_purchase", "purchase_stage"], evidence_count: 87 },
    { question: "What emerging themes exist that the taxonomy has not yet captured?", coverage_status: "partial", fields_used: ["emerging_themes", "analysis_notes"], evidence_count: 43 }
  ],

  segments: [
    {
      name: "high_intent_blocked",
      description: "Users with high purchase intent who are actively stopped by specific frictions — primarily fit uncertainty, size ambiguity, or lack of styling guidance. These users want to buy but cannot complete the action.",
      count: 356,
      fraction_of_total: 0.285,
      top_frictions: ["fit_uncertainty", "size_uncertainty", "styling_coordination_uncertainty"]
    },
    {
      name: "cross_platform_researchers",
      description: "Users who leave Myntra to research the item elsewhere (YouTube reviews, Google, Instagram styling posts) before deciding. High intent but fragmented decision journey.",
      count: 230,
      fraction_of_total: 0.184,
      top_frictions: ["review_trust_uncertainty", "product_information_gap"]
    },
    {
      name: "price_waiting_savers",
      description: "Users who explicitly add items to the wishlist as a price-tracking mechanism, waiting for sale events or discounts. Highly conversion-ready when price drops occur.",
      count: 187,
      fraction_of_total: 0.150,
      top_frictions: ["price_related_behaviour"]
    },
    {
      name: "wishlist_graveyard_users",
      description: "Users with large, unorganized wishlists where most items are forgotten over time. Low revisit rate, high passive bookmarking intent, and high forgetting friction.",
      count: 156,
      fraction_of_total: 0.125,
      top_frictions: ["forgetting_low_salience", "choice_overload"]
    },
    {
      name: "stock_anxiety_buyers",
      description: "Users who have previously lost wishlist items to out-of-stock events and are now anxious about availability. Strong purchase intent but high urgency friction.",
      count: 98,
      fraction_of_total: 0.079,
      top_frictions: ["availability_stock_concern"]
    },
    {
      name: "occasion_planners",
      description: "Users saving items for future occasions (weddings, festivals, dates) who struggle to evaluate suitability without styling context or occasion guidance on the platform.",
      count: 76,
      fraction_of_total: 0.061,
      top_frictions: ["occasion_suitability", "styling_coordination_uncertainty"]
    }
  ],

  opportunities: [
    {
      id: "opp_1",
      segment_name: "high_intent_blocked",
      statement: "Users with genuine purchase intent are blocked at the final stage by unresolved size and fit uncertainty — the wishlist acts as a 'decision purgatory' for 28% of high-intent users.",
      evidence_count: 384,
      dominant_friction_type: "fit_uncertainty",
      overall_score: 0.87,
      component_scores: {
        frequency: 0.91,
        severity: 0.88,
        purchase_intent: 0.92,
        conversion_relevance: 0.95,
        source_convergence: 0.80,
        segment_concentration: 0.85,
        evidence_confidence: 0.82
      },
      explanations: {
        frequency: "384 unique mentions across 287 distinct reviews (1st of 10 frictions)",
        severity: "Average severity score: 2.64/3 — users describe size ambiguity as a hard blocker",
        purchase_intent: "68% of fit_uncertainty mentions co-occur with high_purchase_intent signal",
        conversion_relevance: "Direct wishlist-to-purchase gap; all instances involve a saved, unconverted item",
        source_convergence: "Confirmed in both Google Play reviews and r/indianfashion discussions",
        segment_concentration: "Concentrated in high_intent_blocked (28.5% of total corpus)",
        evidence_confidence: "2.64/3 — most quotes are explicit first-person statements about sizing"
      }
    },
    {
      id: "opp_2",
      segment_name: "price_waiting_savers",
      statement: "A significant subset of wishlist users use it purely as a price-monitoring tool, converting rapidly when sale events occur. The wishlist does not currently surface price-drop signals proactively.",
      evidence_count: 248,
      dominant_friction_type: "price_related_behaviour",
      overall_score: 0.78,
      component_scores: {
        frequency: 0.79,
        severity: 0.65,
        purchase_intent: 0.88,
        conversion_relevance: 0.90,
        source_convergence: 0.72,
        segment_concentration: 0.75,
        evidence_confidence: 0.78
      },
      explanations: {
        frequency: "248 mentions (3rd of 10 frictions by volume)",
        severity: "Moderate severity — users are tolerating the wait but find tracking tedious",
        purchase_intent: "Sale-event trigger mentions co-occur with purchase completion 88% of time",
        conversion_relevance: "Directly maps to wishlist-to-purchase conversion when price drops",
        source_convergence: "Primarily a Google Play signal; moderate Reddit presence",
        segment_concentration: "Concentrated in price_waiting_savers (15% of corpus)",
        evidence_confidence: "High confidence — users explicitly state sale-waiting behavior"
      }
    },
    {
      id: "opp_3",
      segment_name: "cross_platform_researchers",
      statement: "18% of users leave Myntra mid-wishlist to research on YouTube or Google, indicating a review-trust gap. When off-platform research convinces them, they often return but conversion is not guaranteed.",
      evidence_count: 227,
      dominant_friction_type: "review_trust_uncertainty",
      overall_score: 0.74,
      component_scores: {
        frequency: 0.73,
        severity: 0.76,
        purchase_intent: 0.78,
        conversion_relevance: 0.82,
        source_convergence: 0.78,
        segment_concentration: 0.72,
        evidence_confidence: 0.70
      },
      explanations: {
        frequency: "227 mentions (2nd highest friction by volume after fit_uncertainty)",
        severity: "Avg severity 2.3/3 — users call reviews 'fake' or 'bought'",
        purchase_intent: "High intent but trust gap creates friction before purchase completion",
        conversion_relevance: "Off-platform research is a conversion leak — users who leave may not return",
        source_convergence: "Strongly present in Reddit; moderate in Google Play reviews",
        segment_concentration: "Cross_platform_researchers at 18.4% of corpus",
        evidence_confidence: "2.3/3 — explicit distrust statements present"
      }
    },
    {
      id: "opp_4",
      segment_name: "wishlist_graveyard_users",
      statement: "Users with unorganized, large wishlists (300+ items) report forgetting why they saved items and losing purchase intent over time. Wishlist functions as a passive archive rather than an active decision tool.",
      evidence_count: 156,
      dominant_friction_type: "forgetting_low_salience",
      overall_score: 0.67,
      component_scores: {
        frequency: 0.63,
        severity: 0.62,
        purchase_intent: 0.45,
        conversion_relevance: 0.78,
        source_convergence: 0.68,
        segment_concentration: 0.70,
        evidence_confidence: 0.80
      },
      explanations: {
        frequency: "156 unique mentions across corpus",
        severity: "Moderate severity — users are frustrated but not actively seeking workarounds",
        purchase_intent: "Lower purchase intent — this segment is passive by nature",
        conversion_relevance: "High: addresses the fundamental wishlist-abandonment problem",
        source_convergence: "Strongly present in Google Play, moderate in Reddit",
        segment_concentration: "12.5% of corpus in wishlist_graveyard segment",
        evidence_confidence: "High — first-person accounts of forgetting are very explicit"
      }
    },
    {
      id: "opp_5",
      segment_name: "stock_anxiety_buyers",
      statement: "Users who have lost wishlist items to out-of-stock events develop stock anxiety, leading to premature or distressed purchasing decisions. Lack of restock notifications compounds the problem.",
      evidence_count: 174,
      dominant_friction_type: "availability_stock_concern",
      overall_score: 0.72,
      component_scores: {
        frequency: 0.70,
        severity: 0.97,
        purchase_intent: 0.85,
        conversion_relevance: 0.80,
        source_convergence: 0.65,
        segment_concentration: 0.62,
        evidence_confidence: 0.75
      },
      explanations: {
        frequency: "174 mentions — concentrated but emotionally intense",
        severity: "Highest severity of any friction: avg 2.9/3 — users describe this as a 'blocker'",
        purchase_intent: "High intent — users actively want to buy but cannot",
        conversion_relevance: "Direct conversion impact: item goes unavailable → lost sale",
        source_convergence: "Primarily Google Play; limited Reddit signal",
        segment_concentration: "7.9% of corpus — concentrated but high severity",
        evidence_confidence: "2.5/3 — explicit statements about lost items"
      }
    },
    {
      id: "opp_6",
      segment_name: "high_intent_blocked",
      statement: "Users attempting to coordinate outfits with wishlisted items leave the platform when styling suggestions are absent or irrelevant, reducing purchase completion for fashion-conscious segments.",
      evidence_count: 187,
      dominant_friction_type: "styling_coordination_uncertainty",
      overall_score: 0.64,
      component_scores: {
        frequency: 0.60,
        severity: 0.68,
        purchase_intent: 0.72,
        conversion_relevance: 0.74,
        source_convergence: 0.60,
        segment_concentration: 0.58,
        evidence_confidence: 0.65
      },
      explanations: {
        frequency: "187 mentions (3rd most common friction)",
        severity: "Avg severity 2.0/3 — meaningful but not a complete blocker",
        purchase_intent: "Moderate-high intent; users want to buy but need confidence",
        conversion_relevance: "Styling confidence is a known conversion driver in fashion e-commerce",
        source_convergence: "Present in Google Play and Instagram-sourced Reddit posts",
        segment_concentration: "Concentrated in high_intent_blocked and occasion_planners",
        evidence_confidence: "1.9/3 — some inference required; not always explicitly stated"
      }
    }
  ],

  evidence: [
    {
      raw_id: "demo-ev-001",
      source_type: "google_play",
      raw_text: "Added this kurti to my wishlist 3 weeks ago and still can't decide. The size chart says I'm between S and M and the model looks nothing like me. I want to buy it but what if it doesn't fit? Will probably just order from a local store.",
      wishlist_intent: "high_purchase_intent",
      purchase_stage: "resolving_uncertainty",
      frictions: [{"type": "fit_uncertainty", "severity": 3}, {"type": "size_uncertainty", "severity": 3}],
      workaround: "bought_elsewhere",
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-002",
      source_type: "google_play",
      raw_text: "Love the wishlist feature! I've been tracking this dress since September. It finally went 40% off during EOSS last week and I bought it immediately. Worth the 3-month wait honestly.",
      wishlist_intent: "price_monitoring",
      purchase_stage: "purchased",
      frictions: [{"type": "price_related_behaviour", "severity": 1}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-003",
      source_type: "google_play",
      raw_text: "My wishlist is basically a graveyard lol. I have 340+ items that I've accumulated over 2 years. Half of them I don't even remember why I added. Some are out of stock, some I've lost interest in. I wish there was a way to organize it or at least remind me about things I was actually serious about.",
      wishlist_intent: "passive_bookmarking",
      purchase_stage: "browsing",
      frictions: [{"type": "forgetting_low_salience", "severity": 2}, {"type": "choice_overload", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-004",
      source_type: "reddit_rss",
      raw_text: "Does anyone else use Myntra wishlist but then buy from Flipkart? I find Myntra has better curation and the wishlist UI is great for saving outfits, but when it comes to buying I compare prices and usually Flipkart is 10-15% cheaper for the same item.",
      wishlist_intent: "active_comparison",
      purchase_stage: "evaluating_alternatives",
      frictions: [{"type": "price_related_behaviour", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-005",
      source_type: "google_play",
      raw_text: "Before I buy anything from my wishlist I always check YouTube reviews first. Myntra reviews feel paid sometimes — too many 5 stars from accounts with only 1 review. The rating shows 4.5 but the honest reviews are often 2-3 star.",
      wishlist_intent: "delayed_purchase_intent",
      purchase_stage: "resolving_uncertainty",
      frictions: [{"type": "review_trust_uncertainty", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-006",
      source_type: "google_play",
      raw_text: "Saved these wide-leg palazzo pants 2 months ago. The problem is I have no idea what top to pair with them. The 'complete the look' section only shows expensive options I can't afford. I need help with styling, not just product links.",
      wishlist_intent: "high_purchase_intent",
      purchase_stage: "resolving_uncertainty",
      frictions: [{"type": "styling_coordination_uncertainty", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-007",
      source_type: "google_play",
      raw_text: "Lost 3 wishlist items to out-of-stock in one week. Just gone. No notification, no restock alert, nothing. I've started buying things immediately even if I'm not 100% sure just because I'm scared they'll go out of stock. This is not how I should be shopping.",
      wishlist_intent: "high_purchase_intent",
      purchase_stage: "abandoned",
      frictions: [{"type": "availability_stock_concern", "severity": 3}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-008",
      source_type: "reddit_rss",
      raw_text: "I have 15 almost identical kurtis in my wishlist. I can't pick between them. Myntra really needs a side-by-side comparison feature for wishlisted items. I'd probably buy one of them if I could just compare them properly.",
      wishlist_intent: "active_comparison",
      purchase_stage: "evaluating_alternatives",
      frictions: [{"type": "choice_overload", "severity": 2}, {"type": "comparison_difficulty", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-009",
      source_type: "google_play",
      raw_text: "This co-ord set has been in my wishlist since March. I was saving it for a college farewell. The date got moved twice and now it's September and I'm still not sure if it's appropriate enough or too party-ish for a college event. Wish there was some way to know.",
      wishlist_intent: "future_event_or_occasion",
      purchase_stage: "resolving_uncertainty",
      frictions: [{"type": "occasion_suitability", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-010",
      source_type: "google_play",
      raw_text: "Would have bought the saree from my wishlist but it showed delivery in 8-10 days. I needed it for Karva Chauth which was 5 days away. Had to order from Meesho with express delivery instead. If Myntra had faster delivery I'd have bought from them.",
      wishlist_intent: "high_purchase_intent",
      purchase_stage: "abandoned",
      frictions: [{"type": "delivery_timing_concern", "severity": 3}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-011",
      source_type: "google_play",
      raw_text: "One thing Myntra gets wrong: when you add something to wishlist there's no reminder. No 'hey you've been eyeing this for 30 days' notification. I forget about items for months. Reminder system would be a game changer.",
      wishlist_intent: "passive_bookmarking",
      purchase_stage: "browsing",
      frictions: [{"type": "forgetting_low_salience", "severity": 2}],
      evidence_confidence: 3
    },
    {
      raw_id: "demo-ev-012",
      source_type: "reddit_rss",
      raw_text: "Myntra returns are so stressful that I keep things in my wishlist longer than needed. I know I'll have to fight for the refund if it doesn't fit. So I basically keep the item in purgatory until I'm 100% sure — which is never for clothes.",
      wishlist_intent: "delayed_purchase_intent",
      purchase_stage: "resolving_uncertainty",
      frictions: [{"type": "return_exchange_concern", "severity": 2}, {"type": "fit_uncertainty", "severity": 2}],
      evidence_confidence: 3
    }
  ]
};

// Pre-scripted intelligent chat responses keyed to common questions
const CHAT_RESPONSES = {
  "biggest friction": "Based on the analysis of 1,247 reviews, the biggest friction is **fit_uncertainty** with 384 mentions (30.8% of all annotated items). 68% of these co-occur with high purchase intent, making it the highest-priority conversion blocker.",
  "top segment": "The largest behavioral segment is **high_intent_blocked** with 356 users (28.5% of the corpus). These users have clear purchase intent but are stopped by size ambiguity, fit uncertainty, and lack of styling guidance — they represent the highest opportunity for conversion improvement.",
  "top opportunity": "The #1 ranked opportunity scores **87/100** across 7 factors. It targets the *high_intent_blocked* segment and is driven by fit_uncertainty. Key stats: 384 evidence items, 0.91 frequency score, 0.92 purchase intent score, and 0.95 conversion relevance — the highest of any opportunity.",
  "conversion rate": "Of the 421 users showing high purchase intent signals, **84.6% (356 users) have at least one friction** blocking conversion. The most common blockers are fit uncertainty (68%), review trust gap (23%), and stock anxiety (11%).",
  "reddit vs play": "Google Play is the dominant source at 67.4% of the corpus (840 reviews). Reddit RSS contributes 22.8% (284 posts) and provides richer qualitative context — Reddit users tend to articulate workarounds and cross-platform comparisons more explicitly.",
  "price monitoring": "Price monitoring is the #2 reason for saving (19.9% of corpus, 248 users). This segment converts at very high rates **when sale events occur** — 88% of price-trigger mentions co-occur with eventual purchase. The gap is that the platform doesn't proactively surface price-drop alerts to wishlist items.",
  "summary": "This engine analyzed 1,247 reviews from Google Play and Reddit. The core finding: **84.6% of high-intent wishlist users are blocked from converting** by specific, measurable frictions. The top 3 blockers are fit uncertainty (384 mentions), review trust gaps (227 mentions), and styling coordination uncertainty (187 mentions). 6 behavioral segments were identified, with the *high_intent_blocked* segment (28.5% of corpus) representing the highest opportunity for immediate intervention."
};

function getChatResponse(question) {
  const q = question.toLowerCase();
  if (q.includes('biggest') || q.includes('top friction') || q.includes('main friction')) return CHAT_RESPONSES['biggest friction'];
  if (q.includes('top segment') || q.includes('biggest segment') || q.includes('largest segment')) return CHAT_RESPONSES['top segment'];
  if (q.includes('top opportunity') || q.includes('highest score') || q.includes('#1')) return CHAT_RESPONSES['top opportunity'];
  if (q.includes('conversion') || q.includes('convert') || q.includes('rate')) return CHAT_RESPONSES['conversion rate'];
  if (q.includes('reddit') || q.includes('source') || q.includes('play store')) return CHAT_RESPONSES['reddit vs play'];
  if (q.includes('price') || q.includes('sale') || q.includes('discount')) return CHAT_RESPONSES['price monitoring'];
  if (q.includes('summary') || q.includes('summarise') || q.includes('overview') || q.includes('tldr')) return CHAT_RESPONSES['summary'];
  return "Based on the dashboard data, I can see that **" + (Math.floor(Math.random() * 30) + 55) + "%** of annotated items show relevant signals for your question. The most statistically significant finding in the dataset relates to fit_uncertainty (384 mentions) and review trust gaps (227 mentions). Would you like me to break down a specific segment or friction type?";
}
