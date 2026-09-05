"""
Apple App Store Connector for Myntra app reviews.

Uses the app-store-scraper library (public RSS feeds, no auth required).
"""

from datetime import datetime
from typing import List, Optional
from .base import SourceConnector, RawEvidenceItem

MYNTRA_APP_ID = "1106596688"  # Myntra Apple App Store ID


class AppleStoreConnector(SourceConnector):
    """
    Collects public Myntra app reviews from the Apple App Store.

    Source: app-store-scraper (uses Apple's public RSS API)
    Compliance: Public data only, no auth bypass.
    """

    source_name = "apple_store"

    def __init__(self, app_id: str = MYNTRA_APP_ID, country: str = "in", limit: Optional[int] = None):
        self.app_id = app_id
        self.country = country
        self.default_limit = limit

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 200,
    ) -> List[RawEvidenceItem]:
        try:
            from app_store_scraper import AppStore
        except ImportError:
            print(
                "[apple_store] app-store-scraper not installed. "
                "Run: pip install app-store-scraper"
            )
            return []

        try:
            app = AppStore(country=self.country, app_name="myntra", app_id=self.app_id)
            app.review(how_many=limit or self.default_limit or 200)
            raw_reviews = app.reviews
        except Exception as e:
            print(f"[apple_store] Fetch error: {e}")
            return []

        results = []
        for review in raw_reviews:
            text = (review.get("review") or "").strip()
            if not text:
                continue

            published = review.get("date")
            if since and published and published < since:
                continue

            item = RawEvidenceItem(
                source_type=self.source_name,
                source_item_id=str(review.get("reviewId", "")),
                raw_text=text,
                content_hash=RawEvidenceItem.make_hash(text),
                source_url="https://apps.apple.com/in/app/myntra/id1106596688",
                published_at=published,
                rating=float(review.get("rating", 0)) if review.get("rating") else None,
                source_metadata={
                    "title": review.get("title"),
                    "developer_response": review.get("developerResponse"),
                },
            )
            results.append(item)

        print(f"[apple_store] Total collected: {len(results)}")
        return results[: (limit or self.default_limit or 200)]
