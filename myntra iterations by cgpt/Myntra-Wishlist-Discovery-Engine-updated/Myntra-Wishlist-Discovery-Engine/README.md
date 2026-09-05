# Myntra Wishlist AI Discovery Engine

This project collects public fashion-shopping conversations, preprocesses and
annotates them with Gemini, then produces transparent behavioral segments and
opportunity hypotheses for the Myntra wishlist-to-purchase research question.

## Runtime shape

- Railway hosts the FastAPI API and serves the frontend when configured.
- Supabase/PostgreSQL stores raw evidence, annotations, runs, stages, and ranked opportunities.
- GitHub Actions runs the scheduled Python pipeline for free. It is not an always-on worker.
- The dashboard falls back to a clearly labelled curated demo snapshot when the API is unavailable.

## Local setup

1. Copy `.env.example` to `.env` and fill in `DATABASE_URL` and `GEMINI_API_KEY`.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. From the repository root, run `python scripts/db_setup.py` once to apply migrations and seed an empty database.
4. Start the API with `uvicorn backend.app.main:app --reload`.
5. Open `http://localhost:8000/` or serve `frontend/` with any static server.

## GitHub Actions setup

Add these repository secrets:

- `DATABASE_URL`
- `GEMINI_API_KEY`
- Optional: `GEMINI_MODEL`, `PIPELINE_SOURCES`

The workflow runs daily at 1:30 AM IST and can also be started from the Actions
tab. It collects a bounded sample, so the Gemini free-tier request budget is
not allowed to grow without limit.

The dashboard's **Run New Analysis** button queues a run in PostgreSQL. The
workflow processes one queued run when one exists; otherwise it runs one fresh
sample directly. Use **workflow_dispatch** to process a queued run immediately.

## API health and data routes

- `GET /api/health`
- `GET /api/meta/`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/behaviours`
- `GET /api/dashboard/questions`
- `GET /api/segments/`
- `GET /api/segments/opportunities`
- `GET /api/evidence/`
- `POST /api/pipeline/runs`
- `GET /api/pipeline/runs/{run_id}`

Never commit `.env`, database URLs, API keys, service-role keys, or other
credentials. The setup script reads `DATABASE_URL` only from the environment.
