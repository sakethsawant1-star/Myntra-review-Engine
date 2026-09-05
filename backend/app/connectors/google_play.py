"""
Google Play Store Connector for Myntra app reviews.

Uses the google-play-scraper library which fetches public reviews
without bypassing authentication or anti-bot controls.
"""

from datetime import datetime
from typing import List, Optional
from .base import SourceConnector, RawEvidenceItem

MYNTRA_APP_ID = "com.myntra.android"


class GooglePlayConnector(SourceConnector):
    """
    Collects public Myntra app reviews from Google Play Store.

    Source: google-play-scraper (public data, no auth required)
    Compliance: Uses publicly visible review data only.
    """

    source_name = "google_play"

    def __init__(self, app_id: str = MYNTRA_APP_ID, lang: str = "en", country: str = "in", limit: Optional[int] = None):
        self.app_id = app_id
        self.lang = lang
        self.country = country
        self.default_limit = limit

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 200,
    ) -> List[RawEvidenceItem]:
        """
        Fetch public reviews from the Google Play Store.
        Returns up to `limit` reviews for the Myntra app.
        """
        try:
            from google_play_scraper import reviews, Sort
        except ImportError:
            print(
                "[google_play] google-play-scraper not installed. "
                "Run: pip install google-play-scraper"
            )
            return []

        results = []
        count = limit or self.default_limit or 200
        continuation_token = None

        # google-play-scraper returns max 200 per call; paginate if needed
        while len(results) < count:
            batch_size = min(200, count - len(results))
            try:
                batch, continuation_token = reviews(
                    self.app_id,
                    lang=self.lang,
                    country=self.country,
                    sort=Sort.NEWEST,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
            except Exception as e:
                print(f"[google_play] Fetch error: {e}")
                break

            if not batch:
                break

            for review in batch:
                text = (review.get("content") or "").strip()
                if not text:
                    continue

                published = review.get("at")
                if since and published and published < since:
                    # We've reached older reviews than requested
                    return results

                item = RawEvidenceItem(
                    source_type=self.source_name,
                    source_item_id=review.get("reviewId", ""),
                    raw_text=text,
                    content_hash=RawEvidenceItem.make_hash(text),
                    source_url=f"https://play.google.com/store/apps/details?id={self.app_id}",
                    published_at=published,
                    rating=float(review.get("score", 0)) if review.get("score") else None,
                    source_metadata={
                        "app_version": review.get("appVersion"),
                        "thumbs_up": review.get("thumbsUpCount"),
                        "reply_content": review.get("replyContent"),
                    },
                )
                results.append(item)

            if not continuation_token:
                break

        print(f"[google_play] Total collected: {len(results)}")
        return results[:count]
