"""
Phase 6: API Layer — Session management routes.
"""
from fastapi import APIRouter, HTTPException
from app.api.models import SessionCreate, SessionResponse
from app.db.client import get_supabase_client
import logging

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate):
    client = get_supabase_client()
    data = {"title": body.title or "New Chat"}
    try:
        res = client.table("sessions").insert(data).execute()
        return res.data[0]
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Could not create session")


@router.get("")
async def list_sessions():
    client = get_supabase_client()
    try:
        res = client.table("sessions").select("id, title, created_at").order("created_at", desc=True).limit(20).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail="Could not list sessions")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    client = get_supabase_client()
    try:
        res = client.table("sessions").select("*").eq("id", session_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Session not found")
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch session: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch session")


@router.get("/{session_id}/messages")
async def get_messages(session_id: str):
    client = get_supabase_client()
    try:
        res = (
            client.table("messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch messages: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch messages")


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    client = get_supabase_client()
    try:
        client.table("sessions").delete().eq("id", session_id).execute()
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail="Could not delete session")
