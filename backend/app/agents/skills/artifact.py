import logging
from typing import List, Dict, AsyncIterator
from pathlib import Path
from app.agents.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "artifact.md"
ARTIFACT_SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else "Generate a structured artifact."

async def generate_general_artifact(query: str, chunks: List[Dict], history: List[Dict], model_name: str = None) -> AsyncIterator[str]:
    """
    Generates a general structured artifact (table, newsletter, playbook).
    Yields tokens asynchronously for streaming.
    """
    llm = get_llm_provider(model_name)
    
    # Build context string
    blocks = []
    for i, chunk in enumerate(chunks, 1):
        guest = chunk.get("episode", {}).get("guest", "Unknown")
        content = chunk.get("content", "").strip()
        blocks.append(f"Source [{i}] ({guest}):\n{content}")
    
    context_str = "\n\n".join(blocks)
    
    augmented_user_msg = f"## Retrieved Context\n\n{context_str}\n\n---\n**Artifact Request:** {query}"
    
    messages = [
        *history,
        {"role": "user", "content": augmented_user_msg}
    ]
    
    logger.info("Executing General Artifact Generation Skill")
    
    # Yield artifact marker. We default to markdown.
    yield "<artifact type=\"markdown\" title=\"Generated Artifact\">\n"
    
    async for token in llm.stream(
        messages=messages,
        system_prompt=ARTIFACT_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=3000
    ):
        if "<artifact" in token or "</artifact>" in token:
            continue
        yield token
        
    yield "\n</artifact>"
