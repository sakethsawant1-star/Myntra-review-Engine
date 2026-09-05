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

    def collect(self, since: Optional[datetime] = None, limit: Optional[int] = 100, **kwargs) -> List[RawEvidenceItem]:
        """
        Fetch posts from the configured subreddits via RSS.
        """
        items = []
        # Coerce None to default, distribute limit across subreddits
        effective_limit = limit or 100
        limit_per_sub = max(1, effective_limit // len(self.subreddits))

        
        headers = {"User-Agent": self.user_agent}

        for subreddit in self.subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/new.rss"
            print(f"[RedditRSS] Fetching {url}")
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse Atom XML
                root = ET.fromstring(response.content)
                
                # Atom namespace
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entries = root.findall('atom:entry', ns)
                
                sub_count = 0
                for entry in entries:
                    if sub_count >= limit_per_sub:
                        break
                        
                    title = entry.find('atom:title', ns)
                    content = entry.find('atom:content', ns)
                    author = entry.find('atom:author/atom:name', ns)
                    updated = entry.find('atom:updated', ns)
                    link = entry.find('atom:link', ns)
                    id_elem = entry.find('atom:id', ns)
                    
                    title_text = title.text if title is not None else ""
                    content_text = content.text if content is not None else ""
                    
                    # Clean up HTML tags from content (basic cleanup since we have cleaner.py later)
                    import re
                    content_clean = re.sub('<[^<]+>', '', content_text)
                    
                    full_text = f"{title_text}\n\n{content_clean}".strip()
                    if not full_text:
                        continue
                        
                    url_val = link.attrib.get('href', '') if link is not None else ""
                    author_name = author.text if author is not None else "unknown"
                    
                    try:
                        # Format: 2026-09-04T12:00:00+00:00
                        pub_time = datetime.fromisoformat(updated.text.replace('Z', '+00:00')) if updated is not None else datetime.now(timezone.utc)
                    except ValueError:
                        pub_time = datetime.now(timezone.utc)
                        
                    post_id = id_elem.text if id_elem is not None else url_val
                    
                    items.append(
                        RawEvidenceItem(
                            source_type=self.source_name,
                            source_item_id=f"rss_{post_id}",
                            raw_text=full_text,
                            content_hash=RawEvidenceItem.make_hash(full_text),
                            source_metadata={
                                "author": author_name,
                                "url": url_val,
                                "subreddit": subreddit,
                            },
                            published_at=pub_time,
                        )
                    )
                    sub_count += 1
                    
            except Exception as e:
                print(f"[RedditRSS] Error fetching from {subreddit}: {e}")
                
            time.sleep(2) # Be nice to Reddit's servers
            
            if len(items) >= effective_limit:
                break

        return items[:effective_limit]
