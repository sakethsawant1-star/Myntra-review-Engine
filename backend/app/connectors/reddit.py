"""
Reddit Connector for Myntra and fashion shopping discussions.

Uses the PRAW (Python Reddit API Wrapper) library with Reddit's official
public API - no CAPTCHA bypass or auth scraping involved.

Searches subreddits and queries relevant to:
- Myntra app and shopping experience
- Fashion wishlist / save-for-later behaviour
- Online fashion purchase decisions
- Comparison shopping (fit, size, price, trust)
"""

from datetime import datetime, timezone
from typing import List, Optional
from .base import SourceConnector, RawEvidenceItem

# Default subreddits and search queries to seed discovery
DEFAULT_SUBREDDITS = ["india", "IndianFashionAddicts", "frugalmalefashion"]
DEFAULT_QUERIES = [
    "Myntra wishlist",
    "Myntra review purchase",
    "Myntra size fit",
    "Myntra saved items",
    "Myntra vs Ajio",
    "online fashion India buy hesitate",
]


class RedditConnector(SourceConnector):
    """
    Collects public posts and comments from Reddit.

    Source: Reddit official API via PRAW
    Compliance: Read-only, public content only. Requires Reddit API credentials.
    """

    source_name = "reddit"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str = "MyntraDiscoveryEngine/1.0",
        subreddits: Optional[List[str]] = None,
        queries: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.queries = queries or DEFAULT_QUERIES
        self.default_limit = limit

    def _get_reddit_client(self):
        try:
            import praw
        except ImportError:
            raise ImportError(
                "praw not installed. Run: pip install praw"
            )
        return praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 150,
    ) -> List[RawEvidenceItem]:
        """
        Fetch relevant public posts and top-level comments from Reddit.
        Searches across configured subreddits using configured queries.
        """
        reddit = self._get_reddit_client()
        results: List[RawEvidenceItem] = []
        seen_ids = set()
        count = limit or self.default_limit or 150

        for query in self.queries:
            if len(results) >= count:
                break
            try:
                search_results = reddit.subreddit("+".join(self.subreddits)).search(
                    query, sort="relevance", time_filter="year", limit=50
                )
                for submission in search_results:
                    if len(results) >= count:
                        break

                    post_id = f"post_{submission.id}"
                    if post_id not in seen_ids:
                        seen_ids.add(post_id)

                        # Use selftext for text posts, title only for link posts
                        text = submission.selftext.strip() or submission.title.strip()
                        if len(text) < 20:
                            continue

                        published = datetime.fromtimestamp(
                            submission.created_utc, tz=timezone.utc
                        )
                        if since and published < since:
                            continue

                        item = RawEvidenceItem(
                            source_type=self.source_name,
                            source_item_id=post_id,
                            raw_text=text,
                            content_hash=RawEvidenceItem.make_hash(text),
                            source_url=f"https://reddit.com{submission.permalink}",
                            published_at=published,
                            rating=None,
                            source_metadata={
                                "subreddit": str(submission.subreddit),
                                "title": submission.title,
                                "score": submission.score,
                                "num_comments": submission.num_comments,
                                "query_used": query,
                            },
                        )
                        results.append(item)

                    # Also collect top-level comments for richer decision context
                    try:
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:5]:
                            if len(results) >= count:
                                break
                            comment_id = f"comment_{comment.id}"
                            if comment_id in seen_ids:
                                continue
                            seen_ids.add(comment_id)

                            comment_text = (comment.body or "").strip()
                            if len(comment_text) < 20 or comment_text == "[deleted]":
                                continue

                            published_c = datetime.fromtimestamp(
                                comment.created_utc, tz=timezone.utc
                            )
                            if since and published_c < since:
                                continue

                            item = RawEvidenceItem(
                                source_type=self.source_name,
                                source_item_id=comment_id,
                                raw_text=comment_text,
                                content_hash=RawEvidenceItem.make_hash(comment_text),
                                source_url=f"https://reddit.com{submission.permalink}",
                                published_at=published_c,
                                rating=None,
                                source_metadata={
                                    "subreddit": str(submission.subreddit),
                                    "parent_post_title": submission.title,
                                    "parent_post_id": submission.id,
                                    "comment_score": comment.score,
                                    "query_used": query,
                                },
                            )
                            results.append(item)
                    except Exception as e:
                        print(f"[reddit] Comment fetch error on {submission.id}: {e}")

            except Exception as e:
                print(f"[reddit] Search error for query '{query}': {e}")
                continue

        print(f"[reddit] Total collected: {len(results)}")
        return results[:count]
