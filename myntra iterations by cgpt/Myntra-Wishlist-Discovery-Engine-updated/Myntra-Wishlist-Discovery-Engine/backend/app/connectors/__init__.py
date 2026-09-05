"""
Connector registry — maps source names to their connector classes.
Import this to get a connector by name from sources.yaml config.
"""

from .google_play import GooglePlayConnector
from .apple_store import AppleStoreConnector
from .reddit import RedditConnector
from .youtube import YouTubeConnector
from .url_import import UrlImporterConnector

CONNECTOR_REGISTRY = {
    "google_play": GooglePlayConnector,
    "apple_store": AppleStoreConnector,
    "reddit": RedditConnector,
    "youtube": YouTubeConnector,
    "url_import": UrlImporterConnector,
}
