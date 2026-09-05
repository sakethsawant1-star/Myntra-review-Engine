"""
Tests for Phase 3 Deterministic Preprocessing Pipeline
"""

from backend.app.pipeline.preprocessor import Preprocessor
from backend.app.connectors.base import RawEvidenceItem

def test_normalization():
    prep = Preprocessor()
    item = RawEvidenceItem(
        source_type="test", 
        source_item_id="1", 
        raw_text="<p>This is   a test!!!</p>",
        content_hash="h1"
    )
    result = prep.process_item(item)
    assert result["cleaned_text"] == "This is a test!"
    assert result["masked_text"] == "This is a test!"

def test_pii_masking():
    prep = Preprocessor()
    item = RawEvidenceItem(
        source_type="test", 
        source_item_id="2", 
        raw_text="Contact me at test@example.com or call 9876543210. Order no: AWB12345678",
        content_hash="h2"
    )
    result = prep.process_item(item)
    assert "[EMAIL]" in result["masked_text"]
    assert "[PHONE]" in result["masked_text"]
    assert "[ORDER_ID]" in result["masked_text"]
    assert "test@example.com" not in result["masked_text"]
    assert "9876543210" not in result["masked_text"]

def test_spam_detection():
    prep = Preprocessor()
    item = RawEvidenceItem(
        source_type="test", 
        source_item_id="3", 
        raw_text="Use my code for a 50% discount on Myntra!!",
        content_hash="h3"
    )
    result = prep.process_item(item)
    assert result["relevance_status"] == "noise"

def test_short_logistics_complaint_is_noise():
    prep = Preprocessor()
    item = RawEvidenceItem(
        source_type="test",
        source_item_id="4",
        raw_text="Worst courier delivery delayed by 5 days.",
        content_hash="h4"
    )
    result = prep.process_item(item)
    assert result["relevance_status"] == "noise"

def test_candidate_filter():
    prep = Preprocessor()
    # No fashion keywords
    item_rejected = RawEvidenceItem(
        source_type="test",
        source_item_id="5",
        raw_text="This app is really slow and keeps crashing.",
        content_hash="h5"
    )
    # Has fashion keywords
    item_accepted = RawEvidenceItem(
        source_type="test",
        source_item_id="6",
        raw_text="The app keeps crashing when I add items to my wishlist.",
        content_hash="h6"
    )
    
    res1 = prep.process_item(item_rejected)
    assert res1["relevance_status"] == "candidate_rejected"
    
    res2 = prep.process_item(item_accepted)
    # Because it is a candidate, language is detected, it should be 'pending' for AI relevance
    assert res2["relevance_status"] == "pending"

def test_deduplication():
    prep = Preprocessor()
    item1 = RawEvidenceItem(
        source_type="test",
        source_item_id="7",
        raw_text="Love this wishlist feature.",
        content_hash="hash1"
    )
    item2 = RawEvidenceItem(
        source_type="test",
        source_item_id="8",
        raw_text="Love this wishlist feature.",
        content_hash="hash2"
    )
    
    batch = prep.process_batch([item1, item2])
    assert len(batch) == 2
    assert batch[0]["relevance_status"] == "pending"
    assert batch[1]["is_duplicate"] is True
    assert batch[1]["relevance_status"] == "duplicate"
