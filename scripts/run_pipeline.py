"""Run one scheduled or manual pipeline execution.

Configuration is read from environment variables (or a local .env file):
DATABASE_URL, GEMINI_API_KEY, PIPELINE_SCOPE, PIPELINE_CAP, and PIPELINE_SOURCES.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from backend.app.pipeline.pipeline import Pipeline
from backend.app.worker import build_connectors, parse_sources


def main() -> int:
    scope = os.environ.get("PIPELINE_SCOPE", "fresh_sample")
    cap = int(os.environ.get("PIPELINE_CAP", "40"))
    sources = parse_sources(os.environ.get("PIPELINE_SOURCES"))
    connectors = build_connectors(sources)

    if not connectors:
        print(f"No configured connectors available for sources: {sources}")
        return 1

    stats = Pipeline().run(
        connectors=connectors,
        run_type=os.environ.get("PIPELINE_RUN_TYPE", "scheduled"),
        dataset_scope=scope,
        requested_sources=sources,
        item_cap=cap,
    )
    print(f"Done. AI successfully annotated {stats.ai_success} evidence items.")
    return 0 if not stats.warnings else 2


if __name__ == "__main__":
    raise SystemExit(main())
