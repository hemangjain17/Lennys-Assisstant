"""
Phase 6: API Layer — Artifact endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.api.models import ArtifactCreate, ArtifactResponse
from app.db.client import get_supabase_client

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ArtifactResponse, status_code=201)
async def create_artifact(body: ArtifactCreate):
    client = get_supabase_client()
    try:
        res = client.table("artifacts").insert(body.model_dump()).execute()
        return res.data[0]
    except Exception as e:
        logger.error(f"Failed to create artifact: {e}")
        raise HTTPException(status_code=500, detail="Could not create artifact")


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str):
    client = get_supabase_client()
    try:
        res = client.table("artifacts").select("*").eq("id", artifact_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch artifact: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch artifact")


@router.get("/session/{session_id}")
async def list_session_artifacts(session_id: str):
    client = get_supabase_client()
    try:
        res = (
            client.table("artifacts")
            .select("id, type, title, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}")
        raise HTTPException(status_code=500, detail="Could not list artifacts")
