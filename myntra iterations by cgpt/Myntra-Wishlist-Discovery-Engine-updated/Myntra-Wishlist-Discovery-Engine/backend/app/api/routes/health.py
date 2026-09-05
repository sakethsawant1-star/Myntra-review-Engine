from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class HealthResponse(BaseModel):
    status: str
    version: str

@router.get("/health", response_model=HealthResponse)
def get_health():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}
