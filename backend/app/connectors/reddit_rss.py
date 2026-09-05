"""
Reddit RSS Connector for Myntra Wishlist Discovery Engine.

Uses public .rss / .atom feeds from Reddit (e.g., https://www.reddit.com/r/IndianFashionAddicts/new.rss)
Requires no API credentials and bypasses Reddit API limits.
"""

import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional

from backend.app.connectors.base import SourceConnector, RawEvidenceItem

DEFAULT_SUBREDDITS = [
    "india", 
    "IndianFashionAddicts", 
    "frugalmalefashion",
    "InstaCelebsGossip",
    "TwoXIndia"
]

class RedditRSSConnector(SourceConnector):
    """
    Collects public posts from Reddit using their public RSS feeds.
    Compliance: Read-only, public content only. No auth required.
    """

    source_name = "reddit"

    def __init__(
        self,
        subreddits: Optional[List[str]] = None,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ):
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.user_agent = user_agent

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[RawEvidenceItem]:
        results = []
        count = limit or 50

        # Create a unique, descriptive User-Agent as per Reddit's API rules to prevent 429s
        headers = {
            "User-Agent": "MyntraDiscoveryEngine/1.0.0 (by /u/sakethsawant) - automated data collection for research"
        }

        for sub in self.subreddits:
            if len(results) >= count:
                break

            url = f"https://www.reddit.com/r/{sub}/new.json"
            print(f"[Reddit] Fetching {url}")
            try:
                # Add a small delay between requests to be polite
                time.sleep(2)
                response = requests.get(url, headers=headers, timeout=10)
                
                # Check for 429
                if response.status_code == 429:
                    print(f"[Reddit] Error fetching from {sub}: 429 Too Many Requests. Skipping...")
                    continue
                    
                response.raise_for_status()
                
                # Parse JSON
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post_data in posts:
                    if len(results) >= count:
                        break
                        
                    post = post_data.get("data", {})
                    post_id = post.get("id")
                    title = post.get("title", "")
                    selftext = post.get("selftext", "")
                    
                    full_text = f"{title}\n\n{selftext}".strip()
                    if not full_text:
                        continue

                    # Published date (created_utc)
                    created_utc = post.get("created_utc")
                    published = datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else None

                    if since and published and published < since:
                        continue
                        
                    permalink = post.get("permalink", "")
                    source_url = f"https://www.reddit.com{permalink}" if permalink else f"https://www.reddit.com/r/{sub}"

                    item = RawEvidenceItem(
                        source_type=self.source_name,
                        source_item_id=f"{sub}_{post_id}",
                        raw_text=full_text,
                        content_hash=RawEvidenceItem.make_hash(full_text),
                        source_url=source_url,
                        published_at=published,
                        source_metadata={
                            "subreddit": sub,
                            "title": title,
                        },
                    )
                    results.append(item)

            except Exception as e:
                print(f"[Reddit] Error fetching from {sub}: {e}")

        print(f"[reddit] Collected {len(results)} items.")
        return results
