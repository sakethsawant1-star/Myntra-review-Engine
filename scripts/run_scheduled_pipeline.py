"""Process one queued API run, or run a fresh scheduled sample when idle."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from backend.app.worker import run_once
from scripts.run_pipeline import main as run_fresh_sample


if __name__ == "__main__":
    raise SystemExit(0 if run_once() else run_fresh_sample())
