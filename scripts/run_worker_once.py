"""Claim and execute one queued run for GitHub Actions."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from backend.app.worker import run_once


if __name__ == "__main__":
    raise SystemExit(0 if run_once() else 0)
