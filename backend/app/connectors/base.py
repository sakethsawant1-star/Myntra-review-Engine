from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
import hashlib


@dataclass
class RawEvidenceItem:
    """Normalized output from any source connector."""
    source_type: str
    source_item_id: str
    raw_text: str
    content_hash: str
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    rating: Optional[float] = None
    source_metadata: Optional[Dict[str, Any]] = None

    @staticmethod
    def make_hash(text: str) -> str:
        """Create a stable content hash for deduplication."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class SourceConnector(ABC):
    """
    Abstract base class for all source connectors.

    Every connector must:
    - Implement collect() returning a list of RawEvidenceItem
    - Handle its own errors gracefully without raising outside collect()
    - Respect item limits
    - Return an empty list (not raise) when no results are found
    """

    source_name: str = "base"

    @abstractmethod
    def collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[RawEvidenceItem]:
        """
        Collect raw evidence from the source.

        Args:
            since: Only fetch items published after this datetime (optional).
            limit: Maximum number of items to return (optional).

        Returns:
            A list of RawEvidenceItem objects. Returns [] on failure.
        """
        ...

    def _safe_collect(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[RawEvidenceItem]:
        """
        Wraps collect() to ensure errors are logged rather than propagated.
        Use this from the pipeline orchestrator.
        """
        try:
            results = self.collect(since=since, limit=limit)
            print(f"[{self.source_name}] Collected {len(results)} items.")
            return results
        except Exception as e:
            print(f"[{self.source_name}] ERROR during collection: {e}")
            return []
