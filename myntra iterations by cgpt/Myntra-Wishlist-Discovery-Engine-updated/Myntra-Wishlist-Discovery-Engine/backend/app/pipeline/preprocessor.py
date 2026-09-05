import re
import hashlib
from typing import List, Tuple, Set, Dict, Any
from datetime import datetime
import uuid

from backend.app.connectors.base import RawEvidenceItem

# Simple regex patterns for PII
EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'(?:\+91|91)?\s?[6-9]\d{9}' # Indian mobile numbers
ORDER_REGEX = r'(?i)(?:order|tracking|awb)\s*(?:id|no|number)?\s*[:#\-]?\s*([a-zA-Z0-9]{8,15})'

# Spam keywords
PROMO_KEYWORDS = ["use my code", "referral", "discount code", "click here", "subscribe to my channel", "follow me on"]
LOGISTICS_KEYWORDS = ["delivery delayed", "customer care number", "refund not received", "worst courier", "never delivered"]

# Relevance candidates
# Broadened to avoid hypothesis-bias toward any specific friction
FASHION_KEYWORDS = [
    "wishlist", "wish list", "saved", "save for later", "bookmark",
    "size", "fit", "fabric", "material", "look", "wear", "style",
    "bought", "buy", "purchase", "order", "cart", "checkout",
    "compare", "alternative", "similar",
    "ajio", "amazon", "flipkart", "nykaa",
    "quality", "price", "discount", "sale", "offer",
    "review", "rating", "trust", "return", "exchange",
    "try on", "haul", "unboxing",
    "fashion", "outfit", "dress", "shoe", "kurta",
]

class Preprocessor:
    """
    Deterministic Pipeline for cleaning, masking, and filtering RawEvidence.
    """
    
    def __init__(self):
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0
            self._detect_lang = detect
        except ImportError:
            print("[Preprocessor] langdetect not installed. Falling back to english.")
            self._detect_lang = lambda x: 'en'
            
        self.seen_hashes: Set[str] = set()
        
    def _normalize(self, text: str) -> str:
        # Remove basic HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove repeated punctuation
        text = re.sub(r'([.?!])\1+', r'\1', text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def _mask_pii(self, text: str) -> str:
        text = re.sub(EMAIL_REGEX, '[EMAIL]', text)
        text = re.sub(PHONE_REGEX, '[PHONE]', text)
        text = re.sub(ORDER_REGEX, '[ORDER_ID]', text)
        return text

    def _is_spam_or_noise(self, text: str) -> bool:
        lower_text = text.lower()
        if len(lower_text) < 15:
            return True
            
        for promo in PROMO_KEYWORDS:
            if promo in lower_text:
                return True
                
        # If it's purely a logistics complaint (and very short), it might be noise.
        # But we must be careful not to drop long reviews that mention logistics AND fit.
        logistics_count = sum(1 for kw in LOGISTICS_KEYWORDS if kw in lower_text)
        if logistics_count > 0 and len(lower_text) < 100:
            return True
            
        return False

    def _is_relevance_candidate(self, text: str) -> bool:
        """Stage-A cheap candidate filter. If it has no relevant words, mark false."""
        lower_text = text.lower()
        # If any fashion/shopping keyword is present, it's a candidate.
        for kw in FASHION_KEYWORDS:
            if kw in lower_text:
                return True
        return False

    def _make_canonical_hash(self, text: str) -> str:
        """Hash for cross-run deduplication: lowercase, strip whitespace, MD5."""
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def process_item(self, item: RawEvidenceItem) -> Dict[str, Any]:
        """
        Processes a single raw evidence item.
        Returns cleaned_text (normalized) and masked_text (PII-masked) SEPARATELY.
        """
        cleaned = self._normalize(item.raw_text)
        masked = self._mask_pii(cleaned)
        canonical_hash = self._make_canonical_hash(cleaned)
        
        # Deduplication (both within-run and cross-run via canonical_hash)
        is_duplicate = False
        if canonical_hash in self.seen_hashes:
            is_duplicate = True
        else:
            self.seen_hashes.add(canonical_hash)
            
        # Language
        try:
            lang = self._detect_lang(masked)
        except:
            lang = "unknown"
            
        # Relevance
        relevance_status = "pending"
        if is_duplicate:
            relevance_status = "duplicate"
        elif lang != "en":
            relevance_status = "unsupported_language"
        elif self._is_spam_or_noise(masked):
            relevance_status = "noise"
        elif not self._is_relevance_candidate(masked):
            relevance_status = "candidate_rejected"
            
        return {
            "id": str(uuid.uuid4()),
            "raw_evidence_id": item.source_item_id,
            "cleaned_text": cleaned,
            "masked_text": masked,
            "is_duplicate": is_duplicate,
            "relevance_status": relevance_status,
            "language": lang,
            "canonical_hash": canonical_hash,
            "spam_score": None,
        }

    def process_batch(self, items: List[RawEvidenceItem]) -> List[Dict[str, Any]]:
        self.seen_hashes.clear()
        results = []
        for item in items:
            results.append(self.process_item(item))
        return results
