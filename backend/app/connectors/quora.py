"""
Quora Connector for Myntra Wishlist Discovery Engine.

Uses Playwright to bypass Quora's Cloudflare/bot protections and extract answers.
"""

from datetime import datetime
from typing import List, Optional
import time

from backend.app.connectors.base import SourceConnector, RawEvidenceItem

class QuoraConnector(SourceConnector):
    """
    Collects answers from a given list of Quora question URLs using Playwright.
    """
    source_name = "quora"

    def __init__(self, urls: List[str]):
        self.urls = urls

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 20,
    ) -> List[RawEvidenceItem]:
        
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[quora] playwright not installed. Run: pip install playwright && playwright install")
            return []

        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
            
            for url in self.urls:
                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    # Wait for Quora answers to load
                    page.wait_for_selector('div.q-box.qu-pt--medium', timeout=10000)
                    time.sleep(2) # Give it a moment to render dynamic content
                    
                    # Extract answers
                    # Quora's DOM changes frequently. Usually answers are inside q-box with text elements.
                    # We will find the main question title and then the answer blocks.
                    title_elem = page.query_selector('div.q-text.qu-dynamicFontSize--xlarge')
                    title = title_elem.inner_text() if title_elem else "Quora Question"

                    # Answers are typically inside elements that contain user profiles and text.
                    # A robust heuristic is extracting paragraphs inside the main stream.
                    answer_blocks = page.query_selector_all('div.q-box.qu-pt--medium.qu-borderBottom')
                    
                    for block in answer_blocks:
                        if len(results) >= (limit or 20):
                            break
                        
                        text_content = block.inner_text()
                        # Clean up text (remove "Upvote", "Reply" buttons text)
                        clean_text = "\n".join([line for line in text_content.split('\n') if len(line.strip()) > 20 and not line.strip().startswith(('Upvote', 'Reply', 'Share', 'Follow'))])
                        
                        if len(clean_text) < 50:
                            continue

                        item = RawEvidenceItem(
                            source_type=self.source_name,
                            source_item_id=f"quora_{RawEvidenceItem.make_hash(clean_text)[:10]}",
                            raw_text=clean_text,
                            content_hash=RawEvidenceItem.make_hash(clean_text),
                            source_url=url,
                            published_at=None,
                            rating=None,
                            source_metadata={
                                "title": title,
                                "domain": "quora.com"
                            }
                        )
                        results.append(item)
                except Exception as e:
                    print(f"[quora] Failed to fetch {url}: {e}")
                    
            browser.close()

        print(f"[quora] Total collected: {len(results)}")
        return results
