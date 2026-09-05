"""
Tests for Source Connectors - Phase 2

These tests verify:
- Connector output is normalized to RawEvidenceItem
- Stable source IDs are preserved
- Item limits are respected
- Empty results and failures are handled safely
- No duplicate source_item_ids within a single collection run
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from backend.app.connectors.base import RawEvidenceItem, SourceConnector
from backend.app.connectors.google_play import GooglePlayConnector
from backend.app.connectors.reddit import RedditConnector


# ─────────────────────────────────────────────────────────────
# RawEvidenceItem tests
# ─────────────────────────────────────────────────────────────

def test_make_hash_is_stable():
    """Same text always produces same hash."""
    text = "I added this dress to my wishlist"
    assert RawEvidenceItem.make_hash(text) == RawEvidenceItem.make_hash(text)


def test_make_hash_normalizes_whitespace():
    """Extra whitespace should not produce different hashes."""
    h1 = RawEvidenceItem.make_hash("I  added   this")
    h2 = RawEvidenceItem.make_hash("I added this")
    assert h1 == h2


def test_make_hash_case_insensitive():
    h1 = RawEvidenceItem.make_hash("Myntra Wishlist")
    h2 = RawEvidenceItem.make_hash("myntra wishlist")
    assert h1 == h2


# ─────────────────────────────────────────────────────────────
# GooglePlayConnector tests
# ─────────────────────────────────────────────────────────────

MOCK_GOOGLE_PLAY_REVIEW = {
    "reviewId": "gp-test-001",
    "content": "I saved 5 items to my wishlist but could not decide on size.",
    "score": 3,
    "at": datetime(2024, 6, 1, tzinfo=timezone.utc).replace(tzinfo=None),
    "appVersion": "4.5.2",
    "thumbsUpCount": 10,
    "replyContent": None,
}


def test_google_play_returns_raw_evidence_items():
    connector = GooglePlayConnector()
    with patch("google_play_scraper.reviews", return_value=([MOCK_GOOGLE_PLAY_REVIEW], None)):
        result = connector.collect(limit=10)

    assert len(result) == 1
    item = result[0]
    assert isinstance(item, RawEvidenceItem)
    assert item.source_type == "google_play"
    assert item.source_item_id == "gp-test-001"
    assert item.rating == 3.0
    assert item.content_hash != ""


def test_google_play_respects_limit():
    connector = GooglePlayConnector()
    reviews_batch = [MOCK_GOOGLE_PLAY_REVIEW] * 20
    with patch("google_play_scraper.reviews", return_value=(reviews_batch, None)):
        result = connector.collect(limit=5)
    assert len(result) <= 5


def test_google_play_handles_empty_results():
    connector = GooglePlayConnector()
    with patch("google_play_scraper.reviews", return_value=([], None)):
        result = connector.collect(limit=10)
    assert result == []


def test_google_play_handles_network_error():
    connector = GooglePlayConnector()
    with patch("google_play_scraper.reviews", side_effect=Exception("Network error")):
        result = connector._safe_collect(limit=10)
    assert result == []


# ─────────────────────────────────────────────────────────────
# YouTubeConnector tests
# ─────────────────────────────────────────────────────────────

def test_youtube_handles_empty_search():
    from backend.app.connectors.youtube import YouTubeConnector
    connector = YouTubeConnector(api_key="fake")
    with patch.object(connector, "_get_youtube_client") as mock_client:
        mock_yt = MagicMock()
        mock_client.return_value = mock_yt
        # Search returns nothing
        mock_yt.search().list().execute.return_value = {"items": []}
        
        result = connector.collect(limit=10)
    assert result == []


# ─────────────────────────────────────────────────────────────
# UrlImporterConnector tests
# ─────────────────────────────────────────────────────────────

def test_url_importer_returns_raw_evidence():
    from backend.app.connectors.url_import import UrlImporterConnector
    connector = UrlImporterConnector(urls=["http://example.com/fashion"])
    
    mock_html = "<html><title>Fashion Blog</title><body><p>This is a long paragraph about Myntra wishlists that exceeds the forty character minimum limit.</p></body></html>"
    
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        result = connector.collect()
        
    assert len(result) == 1
    item = result[0]
    assert item.source_type == "url_import"
    assert "This is a long paragraph" in item.raw_text
    assert item.source_metadata["domain"] == "example.com"
    assert item.source_metadata["title"] == "Fashion Blog"


# ─────────────────────────────────────────────────────────────
# RedditConnector tests
# ─────────────────────────────────────────────────────────────

def _make_mock_submission(post_id="abc123", title="Myntra wishlist tips", body="I always save items first and compare later."):
    sub = MagicMock()
    sub.id = post_id
    sub.title = title
    sub.selftext = body
    sub.permalink = f"/r/india/comments/{post_id}/"
    sub.created_utc = datetime(2024, 5, 15, tzinfo=timezone.utc).timestamp()
    sub.score = 50
    sub.num_comments = 5
    sub.subreddit = MagicMock()
    sub.subreddit.__str__ = lambda s: "india"
    sub.comments = MagicMock()
    sub.comments.replace_more = MagicMock(return_value=None)
    sub.comments.__iter__ = MagicMock(return_value=iter([]))
    sub.comments.__getitem__ = MagicMock(return_value=[])
    return sub


def test_reddit_returns_raw_evidence_items():
    connector = RedditConnector(client_id="fake", client_secret="fake")
    mock_submission = _make_mock_submission()

    with patch.object(connector, "_get_reddit_client") as mock_client:
        mock_reddit = MagicMock()
        mock_client.return_value = mock_reddit
        mock_reddit.subreddit.return_value.search.return_value = [mock_submission]

        result = connector.collect(limit=10)

    assert len(result) >= 1
    item = result[0]
    assert isinstance(item, RawEvidenceItem)
    assert item.source_type == "reddit"
    assert "post_abc123" == item.source_item_id
    assert item.content_hash != ""


def test_reddit_no_duplicate_ids():
    connector = RedditConnector(client_id="fake", client_secret="fake")
    mock_submission = _make_mock_submission()

    with patch.object(connector, "_get_reddit_client") as mock_client:
        mock_reddit = MagicMock()
        mock_client.return_value = mock_reddit
        # Return same submission across multiple queries to test dedup
        mock_reddit.subreddit.return_value.search.return_value = [mock_submission] * 5

        result = connector.collect(limit=50)

    ids = [item.source_item_id for item in result]
    assert len(ids) == len(set(ids)), "Duplicate source_item_ids found"


def test_reddit_handles_search_error():
    connector = RedditConnector(client_id="fake", client_secret="fake")

    with patch.object(connector, "_get_reddit_client") as mock_client:
        mock_reddit = MagicMock()
        mock_client.return_value = mock_reddit
        mock_reddit.subreddit.return_value.search.side_effect = Exception("API error")

        result = connector._safe_collect(limit=10)

    assert result == []
