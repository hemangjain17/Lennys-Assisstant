"""
Phase 6: API Layer — Chat endpoint with SSE streaming.
POST /chat → persists user message → streams Pi response → persists assistant message.
"""
import json
import logging
import asyncio
import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.api.models import ChatRequest
from app.agents.pi_orchestrator import PiOrchestrator
from app.db.client import get_supabase_client
from app.core.config import settings
from app.agents.llm_provider import GeminiProvider

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

def parse_artifact(full_text: str) -> dict | None:
    """Parses full model response for <artifact> tags and extracts structured fields."""
    if not full_text or "<artifact" not in full_text:
        return None
    match = re.search(r'<artifact type="([^"]+)" title="([^"]+)">([\s\S]*?)</artifact>', full_text)
    if match:
        art_type = match.group(1)
        art_title = match.group(2)
        art_content = match.group(3).strip()
        return {
            "type": art_type if art_type in ("markdown", "html") else "markdown",
            "title": art_title,
            "content": art_content,
            "language": "markdown" if art_type == "markdown" else "html",
        }
    return None


def _save_artifact_if_present(session_id: str, message_id: str, full_text: str):
    """Parses full response for <artifact> tags and persists to Supabase DB with version tracking."""
    artifact = parse_artifact(full_text)
    if not artifact or not message_id:
        return
    
    client = get_supabase_client()
    current_version = 1

    try:
        existing_res = (
            client.table("artifacts")
            .select("version")
            .eq("session_id", session_id)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        if existing_res.data and len(existing_res.data) > 0:
            current_version = (existing_res.data[0].get("version") or 1) + 1
    except Exception:
        current_version = 1

    payload = {
        "session_id": session_id,
        "message_id": message_id,
        "type": artifact["type"],
        "title": artifact["title"],
        "content": artifact["content"],
        "language": artifact["language"],
        "version": current_version,
        "metadata": {
            "generated_by": "pi_orchestrator",
            "char_length": len(artifact["content"]),
        },
    }

    try:
        res = client.table("artifacts").insert(payload).execute()
        artifact_id = res.data[0]["id"] if res.data else None
        logger.info(f"Persisted artifact '{artifact['title']}' (v{current_version}, ID: {artifact_id}) to Supabase")
        return artifact_id
    except Exception as e:
        logger.warning(f"Full artifact insert failed ({e}). Retrying with base fields...")
        try:
            base_payload = {
                "session_id": session_id,
                "message_id": message_id,
                "type": artifact["type"],
                "title": artifact["title"],
                "content": artifact["content"],
                "language": artifact["language"],
            }
            res = client.table("artifacts").insert(base_payload).execute()
            artifact_id = res.data[0]["id"] if res.data else None
            logger.info(f"Persisted base artifact '{artifact['title']}' (ID: {artifact_id}) to Supabase")
            return artifact_id
        except Exception as retry_err:
            logger.error(f"Failed to save artifact to DB: {retry_err}")
            return None

def _save_retrieval_trace(
    session_id: str,
    message_id: str,
    query: str,
    chunks: list,
    rewritten_query: str = None,
    subqueries: list = None,
    grounding_result: dict = None,
    strategy: str = "hybrid_rrf_cohere_mmr",
):
    """Persists retrieval trace, chunk selection metadata, and grounding verification to Supabase DB."""
    if not message_id or not chunks:
        return
    try:
        chunk_ids = [c.get("id") for c in chunks if c.get("id")]
        client = get_supabase_client()
        payload = {
            "session_id": session_id,
            "message_id": message_id,
            "original_query": query,
            "rewritten_query": rewritten_query,
            "subqueries": subqueries,
            "strategy": strategy,
            "candidate_count": len(chunks),
            "selected_chunks": chunk_ids,
        }
        if grounding_result:
            payload["latencies"] = {"grounding_verification": grounding_result}
            
        client.table("retrieval_traces").insert(payload).execute()
        logger.info(f"Saved retrieval trace for message {message_id}")
    except Exception as e:
        logger.error(f"Failed to save retrieval trace: {e}")

async def _generate_and_save_title(session_id: str, first_message: str) -> str:
    client = get_supabase_client()
    words = [w for w in first_message.strip().split() if w]
    fallback_title = " ".join(words[:4]).title() if words else "Chat"
    if len(fallback_title) > 30:
        fallback_title = fallback_title[:27] + "..."
        
    try:
        # Set fallback immediately so it's never stuck on "New Chat"
        client.table("sessions").update({"title": fallback_title}).eq("id", session_id).execute()

        llm = GeminiProvider(model_name=settings.gemini_model_name or "gemini-3-flash-preview")
        title_prompt = "Summarize the user question into a clean 3 to 5 word topic title for a chat thread. Output ONLY the title text. Do not use quotes or punctuation."
        llm_title = await llm.generate(
            messages=[{"role": "user", "content": first_message}],
            system_prompt=title_prompt,
            max_tokens=20
        )
        if llm_title and len(llm_title.strip()) > 1:
            clean_title = llm_title.strip().strip('"').strip("'").strip(".").title()
            client.table("sessions").update({"title": clean_title}).eq("id", session_id).execute()
            logger.info(f"Updated session {session_id} title to: {clean_title}")
            return clean_title
    except Exception as e:
        logger.error(f"Failed to generate title: {e}")
        
    return fallback_title

def _load_history(session_id: str, limit: int = 10) -> list:
    """Fetch last N messages from Supabase for conversation context."""
    client = get_supabase_client()
    try:
        res = (
            client.table("messages")
            .select("role, content")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        # Reverse so oldest first
        return list(reversed(res.data or []))
    except Exception:
        return []


def _save_message(session_id: str, role: str, content: str, model_provider: str = None, model_name: str = None) -> str:
    """Persist a message to Supabase and return its ID."""
    client = get_supabase_client()
    try:
        res = client.table("messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content,
            "model_provider": model_provider,
            "model_name": model_name,
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return None


@router.post("")
async def chat(body: ChatRequest, background_tasks: BackgroundTasks):
    """
    Streams the assistant response via Server-Sent Events (SSE).
    
    Event types emitted:
      data: {"type": "token", "text": "..."}     - streaming token
      data: {"type": "done", "message_id": "...", "title": "..."}  - stream finished
      data: {"type": "error", "message": "..."}    - error occurred
    """
    # 1. Persist user message
    user_msg_id = _save_message(body.session_id, "user", body.message)

    # 2. Load conversation history
    history = _load_history(body.session_id, limit=8)
    
    # 2.5 Generate title if it's the first message
    new_title = None
    if len(history) <= 1:
        new_title = await _generate_and_save_title(body.session_id, body.message)

    orchestrator = PiOrchestrator(model_name=body.model)

    async def event_stream():
        full_response = []
        try:
            async for item in orchestrator.run(
                query=body.message,
                history=history,
                session_id=body.session_id,
            ):
                if isinstance(item, str) and item.startswith('{"type": "status"'):
                    yield f"data: {item}\n\n"
                else:
                    full_response.append(item)
                    yield f"data: {json.dumps({'type': 'token', 'text': item})}\n\n"

            # 3. Persist assistant message after stream completes
            full_text = "".join(full_response)
            assistant_msg_id = _save_message(
                body.session_id,
                "assistant",
                full_text,
                model_provider=body.model or "gemini",
                model_name=settings.gemini_model_name,
            )

            # 3.5 Persist retrieval traces & artifacts if present
            if assistant_msg_id:
                if orchestrator.last_retrieved_chunks:
                    _save_retrieval_trace(
                        session_id=body.session_id,
                        message_id=assistant_msg_id,
                        query=body.message,
                        chunks=orchestrator.last_retrieved_chunks,
                        rewritten_query=orchestrator.rewritten_query,
                        subqueries=orchestrator.subqueries,
                        grounding_result=orchestrator.grounding_result,
                    )
                _save_artifact_if_present(body.session_id, assistant_msg_id, full_text)
            
            done_payload = {"type": "done", "message_id": assistant_msg_id}
            if new_title:
                done_payload["title"] = new_title
                
            yield f"data: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
