"""
FastAPI entry point for the Myntra Wishlist AI Discovery Engine.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env early so DATABASE_URL, GEMINI_API_KEY etc. are available to all routes
from dotenv import load_dotenv
load_dotenv()

from backend.app.api.routes import health, dashboard, pipeline, meta, evidence, segments, chat

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="Myntra Wishlist Discovery API",
    description="API for accessing AI behavioural annotations and ranked opportunities.",
    version="2.0.0",
)

origins = [origin.strip() for origin in os.environ.get("FRONTEND_ORIGINS", "*").split(",") if origin.strip()]
allow_credentials = origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(meta.router)
app.include_router(dashboard.router)
app.include_router(evidence.router)
app.include_router(segments.router)
app.include_router(pipeline.router)
app.include_router(chat.router)

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"message": "Welcome to the Myntra Wishlist Discovery Engine API. See /docs for endpoints."}
