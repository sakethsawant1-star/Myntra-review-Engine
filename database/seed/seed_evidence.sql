-- Mock Seed Data for Myntra AI Discovery Engine

INSERT INTO collection_runs (id, run_type, status, source_config_version, dataset_scope, items_collected, items_retained) 
VALUES ('c1a4e12e-13c5-430f-b4de-122e2397c7d1', 'manual', 'completed', 'v2.0.0', 'fresh_sample', 15, 15);

-- 1. Relevant wishlist behaviour (high intent, friction on fit)
INSERT INTO raw_evidence (id, source_type, source_item_id, raw_text, rating, content_hash, collection_run_id) 
VALUES ('e1111111-1111-1111-1111-111111111111', 'google_play', 'gp-101', 'I added 3 dresses to my wishlist last week. Wanted to buy the blue one for a wedding, but I am not sure if the waist will fit tight or loose. The size chart is confusing.', 4, 'hash_101', 'c1a4e12e-13c5-430f-b4de-122e2397c7d1');

-- 2. Generic app complaint (low/no relevance)
INSERT INTO raw_evidence (id, source_type, source_item_id, raw_text, rating, content_hash, collection_run_id) 
VALUES ('e2222222-2222-2222-2222-222222222222', 'google_play', 'gp-102', 'App keeps crashing when I open the cart. Fix this immediately.', 1, 'hash_102', 'c1a4e12e-13c5-430f-b4de-122e2397c7d1');

-- 3. Comparison behaviour
INSERT INTO raw_evidence (id, source_type, source_item_id, raw_text, rating, content_hash, collection_run_id) 
VALUES ('e3333333-3333-3333-3333-333333333333', 'reddit', 'rd-101', 'Does anyone else just save 20 pairs of sneakers to their Myntra wishlist and then go check Amazon and Flipkart to see who has the best price? I ended up buying on Ajio because it was cheaper.', NULL, 'hash_103', 'c1a4e12e-13c5-430f-b4de-122e2397c7d1');

-- 4. Unclear intent (bookmarking)
INSERT INTO raw_evidence (id, source_type, source_item_id, raw_text, rating, content_hash, collection_run_id) 
VALUES ('e4444444-4444-4444-4444-444444444444', 'apple_store', 'as-101', 'I love the new UI update, much easier to just heart things and save them for later fashion inspiration.', 5, 'hash_104', 'c1a4e12e-13c5-430f-b4de-122e2397c7d1');

-- 5. Off-platform research workaround
INSERT INTO raw_evidence (id, source_type, source_item_id, raw_text, rating, content_hash, collection_run_id) 
VALUES ('e5555555-5555-5555-5555-555555555555', 'youtube', 'yt-101', 'This review really helped. I had this HRX jacket in my Myntra wishlist for a month because there were no photos of real people wearing it. After seeing this video I finally bought it.', NULL, 'hash_105', 'c1a4e12e-13c5-430f-b4de-122e2397c7d1');

-- 6. Contradictory evidence (price vs quality)
INSERT INTO raw_evidence (id, source_type, source_item_id, raw_text, rating, content_hash, collection_run_id) 
VALUES ('e6666666-6666-6666-6666-666666666666', 'reddit', 'rd-102', 'Honestly, I dont care about the price. I wishlist things on Myntra and wait because I am worried about whether the material is actually cotton or that weird synthetic blend. Price drops don''t make me buy.', NULL, 'hash_106', 'c1a4e12e-13c5-430f-b4de-122e2397c7d1');

-- Insert Processed Evidence for these 6 items
INSERT INTO processed_evidence (id, raw_evidence_id, cleaned_text, is_duplicate, relevance_status)
VALUES 
('f1111111-1111-1111-1111-111111111111', 'e1111111-1111-1111-1111-111111111111', 'I added 3 dresses to my wishlist last week. Wanted to buy the blue one for a wedding, but I am not sure if the waist will fit tight or loose. The size chart is confusing.', FALSE, 'relevant'),
('f2222222-2222-2222-2222-222222222222', 'e2222222-2222-2222-2222-222222222222', 'App keeps crashing when I open the cart. Fix this immediately.', FALSE, 'irrelevant'),
('f3333333-3333-3333-3333-333333333333', 'e3333333-3333-3333-3333-333333333333', 'Does anyone else just save 20 pairs of sneakers to their Myntra wishlist and then go check Amazon and Flipkart to see who has the best price? I ended up buying on Ajio because it was cheaper.', FALSE, 'relevant'),
('f4444444-4444-4444-4444-444444444444', 'e4444444-4444-4444-4444-444444444444', 'I love the new UI update, much easier to just heart things and save them for later fashion inspiration.', FALSE, 'relevant_low_intent'),
('f5555555-5555-5555-5555-555555555555', 'e5555555-5555-5555-5555-555555555555', 'This review really helped. I had this HRX jacket in my Myntra wishlist for a month because there were no photos of real people wearing it. After seeing this video I finally bought it.', FALSE, 'relevant'),
('f6666666-6666-6666-6666-666666666666', 'e6666666-6666-6666-6666-666666666666', 'Honestly, I dont care about the price. I wishlist things on Myntra and wait because I am worried about whether the material is actually cotton or that weird synthetic blend. Price drops dont make me buy.', FALSE, 'relevant');

-- Example of an annotation on the first processed item
INSERT INTO evidence_annotations (id, processed_evidence_id, wishlist_relevance, wishlist_intent, purchase_stage, off_platform_research, workaround, frictions, evidence_confidence, analysis_notes)
VALUES 
('a1111111-1111-1111-1111-111111111111', 'f1111111-1111-1111-1111-111111111111', 'high', 'genuine_purchase_consideration', 'evaluating_alternatives', '[]', 'none', '[{"type": "fit_uncertainty", "label": "waist fit", "severity": 2, "support_span": "not sure if the waist will fit tight or loose"}, {"type": "product_information_gap", "label": "confusing size chart", "severity": 2, "support_span": "The size chart is confusing."}]', 3, 'User shows high intent for an upcoming event but is blocked by fit uncertainty and a confusing size chart.');
