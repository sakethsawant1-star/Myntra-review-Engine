"""Pipeline worker used by GitHub Actions and optional local development.

The API only queues work. This module claims queued runs and executes them in
the same process, so a paid always-on worker is not required.
"""

import json
import os
import time
from typing import Iterable, List, Optional

import psycopg2
import psycopg2.extras

from backend.app.connectors.apple_store import AppleStoreConnector
from backend.app.connectors.google_play import GooglePlayConnector
from backend.app.connectors.reddit import RedditConnector
from backend.app.connectors.reddit_rss import RedditRSSConnector
from backend.app.connectors.youtube import YouTubeConnector
from backend.app.connectors.quora import QuoraConnector
from backend.app.pipeline.pipeline import Pipeline


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL must be set for worker.")
    return url


def parse_sources(value: Optional[object]) -> List[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = value.split(",")
    if not value:
        value = os.environ.get("PIPELINE_SOURCES", "google_play,reddit_rss,quora").split(",")
    return list(dict.fromkeys(str(source).strip() for source in value if str(source).strip()))


def build_connectors(sources: Iterable[str]):
    """Build connectors without passing collection limits to constructors."""
    normalized = {source.strip().lower() for source in sources}
    connectors = []

    if "quora" in normalized:
        connectors.append(QuoraConnector(urls=["https://www.quora.com/What-are-the-best-clothes-shopping-apps-in-India"]))
    if "google_play" in normalized:
        connectors.append(GooglePlayConnector())
    if "apple_store" in normalized:
        connectors.append(AppleStoreConnector())
    if "reddit_rss" in normalized or "reddit" in normalized and not os.environ.get("REDDIT_CLIENT_ID"):
        connectors.append(RedditRSSConnector())
    if "reddit" in normalized and os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"):
        connectors.append(
            RedditConnector(
                client_id=os.environ["REDDIT_CLIENT_ID"],
                client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            )
        )
    if "youtube" in normalized and os.environ.get("YOUTUBE_API_KEY"):
        connectors.append(YouTubeConnector(api_key=os.environ["YOUTUBE_API_KEY"]))

    return connectors


def claim_next_run(conn) -> Optional[dict]:
    """Atomically claim the oldest queued run."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, dataset_scope, requested_item_cap, requested_sources
            FROM collection_runs
            WHERE status = 'queued'
            ORDER BY COALESCE(requested_at, started_at) ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            "UPDATE collection_runs SET status = 'running', heartbeat_at = NOW() WHERE id = %s",
            (row["id"],),
        )
        conn.commit()
        return dict(row)


def _mark_failed(run_id: str, message: str) -> None:
    try:
        with psycopg2.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE collection_runs SET status='failed', error_summary=%s, completed_at=NOW() WHERE id=%s",
                    (message[:2000], run_id),
                )
            conn.commit()
    except Exception as exc:
        print(f"[Worker] Could not mark run {run_id} failed: {exc}")


def execute_run(run_data: dict):
    run_id = str(run_data["id"])
    scope = run_data.get("dataset_scope") or os.environ.get("PIPELINE_SCOPE", "fresh_sample")
    cap = int(run_data.get("requested_item_cap") or os.environ.get("PIPELINE_CAP", 40))
    sources = parse_sources(run_data.get("requested_sources"))
    print(f"[Worker] Claimed run {run_id}. Scope: {scope}, Cap: {cap}, Sources: {sources}")

    try:
        connectors = build_connectors(sources)
        if not connectors:
            raise RuntimeError("No configured connectors available")
        return Pipeline().run(
            connectors=connectors,
            run_type="worker_trigger",
            dataset_scope=scope,
            item_cap=cap,
            requested_sources=sources,
            run_id=run_id,
        )
    except Exception as exc:
        print(f"[Worker] Fatal error executing run {run_id}: {exc}")
        _mark_failed(run_id, str(exc))
        return None


def run_once() -> bool:
    """Claim and execute one queued run; return whether work was found."""
    with psycopg2.connect(get_db_url()) as conn:
        run_data = claim_next_run(conn)
    if not run_data:
        print("[Worker] No queued pipeline runs.")
        return False
    execute_run(run_data)
    return True


def start_worker(poll_interval: int = 5):
    print(f"[Worker] Started polling every {poll_interval}s.")
    while True:
        try:
            if not run_once():
                time.sleep(poll_interval)
        except Exception as exc:
            print(f"[Worker] Database connection error: {exc}")
            time.sleep(poll_interval)


if __name__ == "__main__":
    if "--once" in os.sys.argv:
        run_once()
    else:
        start_worker()
