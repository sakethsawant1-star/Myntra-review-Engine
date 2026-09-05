"""
Meta API Routes
Returns system methodology, configured sources, and versions.
"""

from fastapi import APIRouter
import os

router = APIRouter(prefix="/api/meta", tags=["Metadata"])

@router.get("/")
def get_meta():
    """Returns engine methodology metadata for the UI."""
    return {
        "engine_version": "v2.0.0",
        "configured_sources": {
            "google_play": True,
            "apple_store": True,
            "reddit_rss": True,
            "youtube": bool(os.environ.get("YOUTUBE_API_KEY")),
            "reddit": bool(os.environ.get("REDDIT_CLIENT_ID")),
        },
        "methodology": {
            "focus": "Wishlist-to-purchase conversion blockers",
            "scoring": "7-factor transparent weighting",
            "evidence_confidence": "Validated exact span extraction"
        }
    }
