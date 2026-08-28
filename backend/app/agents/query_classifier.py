"""
Phase 5: Query Classifier
Classifies user queries to determine retrieval strategy and response type.
Uses lightweight Gemini call with a small prompt.
"""
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)


class QueryType(str, Enum):
    SIMPLE = "simple"        # Single-episode factual lookup
    COMPLEX = "complex"      # Multi-episode synthesis / comparison
    ARTIFACT = "artifact"    # Requests a structured output (table, essay, newsletter)
    CHITCHAT = "chitchat"    # Greeting / off-topic, no retrieval needed


# Load the classifier prompt from the prompts folder
PROMPT_PATH = Path(__file__).parent / "prompts" / "query_classifier.md"
CLASSIFICATION_SYSTEM = (
    PROMPT_PATH.read_text(encoding="utf-8")
    if PROMPT_PATH.exists()
    else "You are a query router for a podcast knowledge base assistant."
)


def format_history(history: Optional[List[Dict]]) -> str:
    """Formats conversation history for inclusion in prompts."""
    if not history:
        return "No conversation history."
    formatted = []
    for turn in history:
        role = "User" if turn.get("role") == "user" else "Assistant"
        content = turn.get("content", "").strip()
        # Truncate content if it contains retrieved context blocks to avoid prompt bloat/noise
        if "## Retrieved Context" in content:
            content = content.split("## Retrieved Context")[0].strip() + "\n[Retrieved Context Omitted]"
        if len(content) > 300:
            content = content[:300] + "..."
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)


async def classify_query(query: str, history: Optional[List[Dict]] = None, model_name: str = None) -> Dict:
    """
    Returns a dict: { type: QueryType, intent: str, requires_rag: bool, is_follow_up: bool, requires_multi_query: bool, requires_citations: bool, focused_guest: Optional[str], reason: str }
    Falls back to "complex" on API error.
    """
    classifier_model = model_name or settings.gemini_model_name
    url = GEMINI_URL.format(model=classifier_model, key=settings.gemini_api_key)

    if not settings.gemini_api_key:
        return {
            "type": QueryType.COMPLEX,
            "intent": "product_strategy",
            "requires_rag": True,
            "is_follow_up": False,
            "requires_multi_query": True,
            "requires_citations": True,
            "focused_guest": None,
            "reason": "No API key, defaulting to complex",
        }

    try:
        history_str = format_history(history)
        system_instruction = CLASSIFICATION_SYSTEM.replace("{query}", query).replace("{history_context}", history_str)

        body = {
            "contents": [{"role": "user", "parts": [{"text": query}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 256,
                "responseMimeType": "application/json"
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
        raw_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(raw_text.strip())
        result["type"] = QueryType(result.get("type", "complex"))
        return result
    except Exception as e:
        logger.warning(f"Query classification failed: {e}. Defaulting to complex.")
        return {
            "type": QueryType.COMPLEX,
            "intent": "product_strategy",
            "requires_rag": True,
            "is_follow_up": False,
            "requires_multi_query": True,
            "requires_citations": True,
            "focused_guest": None,
            "reason": f"Classification failed: {e}",
        }
