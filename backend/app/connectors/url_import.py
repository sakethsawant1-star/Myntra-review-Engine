"""
Generic URL Importer for public fashion blogs and forum posts.

Uses requests and BeautifulSoup to fetch and extract text from a given web page.
"""

from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse
from .base import SourceConnector, RawEvidenceItem

class UrlImporterConnector(SourceConnector):
    """
    Collects text content from a given list of public URLs.
    
    Source: Direct HTTP fetch and HTML parsing
    Compliance: Respects standard web scraping practices. Intended for public blogs/articles.
    """

    source_name = "url_import"

    def __init__(self, urls: List[str]):
        """
        Args:
            urls: A list of public URLs to scrape.
        """
        self.urls = urls

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[RawEvidenceItem]:
        
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            print(
                "[url_import] beautifulsoup4 or requests not installed. "
                "Run: pip install beautifulsoup4 requests"
            )
            return []

        results = []
        count = limit or len(self.urls) * 5  # Arbitrary limit if None
        
        # We process up to count items (we might extract multiple paragraphs/comments per URL)
        for url in self.urls:
            if len(results) >= count:
                break
                
            try:
                headers = {
                    "User-Agent": "MyntraDiscoveryEngine/1.0 (Research/Academic Project)"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract main text. A simple heuristic: get all paragraph tags
                # For more complex forums, specific CSS selectors might be needed.
                paragraphs = soup.find_all("p")
                domain = urlparse(url).netloc
                
                extracted_text = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 40: # Only keep substantial paragraphs
                        extracted_text.append(text)
                
                if not extracted_text:
                    continue
                
                # Combine all extracted paragraphs into one item representing the page content
                # Alternatively, we could yield each paragraph as a separate item.
                full_content = "\n\n".join(extracted_text)
                
                item = RawEvidenceItem(
                    source_type=self.source_name,
                    source_item_id=f"url_{RawEvidenceItem.make_hash(url)[:12]}",
                    raw_text=full_content,
                    content_hash=RawEvidenceItem.make_hash(full_content),
                    source_url=url,
                    published_at=None, # Often hard to reliably extract from random pages
                    rating=None,
                    source_metadata={
                        "domain": domain,
                        "title": soup.title.string if soup.title else None
                    },
                )
                results.append(item)
                
            except Exception as e:
                print(f"[url_import] Failed to fetch {url}: {e}")
                continue

        print(f"[url_import] Total collected: {len(results)}")
        return results[:count]
