import logging
from typing import List, Dict, AsyncIterator
from pathlib import Path
from app.agents.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "ship30.md"
SHIP30_SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else "Write a Ship 30 for 30 essay based on the context."

async def generate_ship30_essay(query: str, chunks: List[Dict], history: List[Dict], model_name: str = None) -> AsyncIterator[str]:
    """
    Generates a Ship 30 for 30 style essay using the provided chunks.
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
    
    augmented_user_msg = f"## Retrieved Context\n\n{context_str}\n\n---\n**Topic Request:** {query}"
    
    messages = [
        *history,
        {"role": "user", "content": augmented_user_msg}
    ]
    
    logger.info("Executing Ship30 Generation Skill")
    
    # Extract short title from topic request if possible
    clean_topic = query.replace("Turn the", "").replace("Write a", "").replace("Ship 30 for 30 essay on", "").replace("essay", "").strip().title()
    art_title = f"Ship 30: {clean_topic[:35]}" if clean_topic else "Ship 30 for 30 Essay"
    
    # We yield a special marker to tell the frontend this is an artifact
    yield f'<artifact type="markdown" title="{art_title}">\n'
    
    async for token in llm.stream(
        messages=messages,
        system_prompt=SHIP30_SYSTEM_PROMPT,
        temperature=0.4,
        max_tokens=3000
    ):
        if "<artifact" in token or "</artifact>" in token:
            continue
        yield token
        
    yield "\n</artifact>"
