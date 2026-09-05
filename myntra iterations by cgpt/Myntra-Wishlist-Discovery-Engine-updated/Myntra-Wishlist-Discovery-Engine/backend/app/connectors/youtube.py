"""
YouTube Connector for fashion haul and review comments.

Uses the YouTube Data API v3 to fetch comments on specific videos
or search for videos related to Myntra and fetch their comments.
"""

from datetime import datetime, timezone
from typing import List, Optional
from .base import SourceConnector, RawEvidenceItem

DEFAULT_VIDEO_QUERIES = [
    "Myntra haul 2024",
    "Myntra review",
    "Myntra try on haul",
]


class YouTubeConnector(SourceConnector):
    """
    Collects public comments from YouTube videos related to Myntra.

    Source: YouTube Data API v3
    Compliance: Public data only. Requires YouTube API Key.
    """

    source_name = "youtube"

    def __init__(
        self,
        api_key: str,
        video_ids: Optional[List[str]] = None,
        search_queries: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ):
        self.api_key = api_key
        # We can either provide specific video IDs to scrape, or search queries to find videos
        self.video_ids = video_ids or []
        self.search_queries = search_queries or DEFAULT_VIDEO_QUERIES
        self.default_limit = limit

    def _get_youtube_client(self):
        try:
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "google-api-python-client not installed. "
                "Run: pip install google-api-python-client"
            )
        return build("youtube", "v3", developerKey=self.api_key, cache_discovery=False)

    def _search_videos(self, youtube, query: str, max_results: int = 5) -> List[str]:
        try:
            request = youtube.search().list(
                part="id",
                q=query,
                type="video",
                maxResults=max_results,
                order="relevance",
            )
            response = request.execute()
            return [item["id"]["videoId"] for item in response.get("items", [])]
        except Exception as e:
            print(f"[youtube] Error searching for videos with query '{query}': {e}")
            return []

    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = 200,
    ) -> List[RawEvidenceItem]:
        
        youtube = self._get_youtube_client()
        results: List[RawEvidenceItem] = []
        count = limit or self.default_limit or 200
        
        # 1. Gather target video IDs
        target_video_ids = set(self.video_ids)
        if not target_video_ids:
            for query in self.search_queries:
                vids = self._search_videos(youtube, query, max_results=3)
                target_video_ids.update(vids)

        # 2. Fetch comments for each video
        for video_id in target_video_ids:
            if len(results) >= count:
                break
                
            try:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=100,
                    textFormat="plainText"
                )
                
                while request and len(results) < count:
                    response = request.execute()
                    
                    for item in response.get("items", []):
                        if len(results) >= count:
                            break
                            
                        comment = item["snippet"]["topLevelComment"]["snippet"]
                        text = comment.get("textDisplay", "").strip()
                        
                        if len(text) < 15:
                            continue  # Skip very short/useless comments
                            
                        published_str = comment.get("publishedAt")
                        published = None
                        if published_str:
                            # Parse ISO 8601 string returned by YouTube (e.g. 2024-05-21T15:32:00Z)
                            published = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            
                        if since and published and published < since:
                            continue
                            
                        comment_id = item.get("id")
                        
                        raw_item = RawEvidenceItem(
                            source_type=self.source_name,
                            source_item_id=f"yt_{comment_id}",
                            raw_text=text,
                            content_hash=RawEvidenceItem.make_hash(text),
                            source_url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                            published_at=published,
                            rating=None,
                            source_metadata={
                                "video_id": video_id,
                                "author": comment.get("authorDisplayName"),
                                "like_count": comment.get("likeCount", 0)
                            },
                        )
                        results.append(raw_item)
                        
                    request = youtube.commentThreads().list_next(request, response)
                    
            except Exception as e:
                # If comments are disabled for a video, it throws a 403. Just skip.
                print(f"[youtube] Error fetching comments for video {video_id}: {e}")
                continue

        print(f"[youtube] Total collected: {len(results)}")
        return results[:count]
