import asyncio
import logging
import random
from typing import List

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class Embedder:
    """
    Generates embeddings via Gemini API.
    Handles 429 Rate Limits with exponential backoff.
    """

    def __init__(self):
        # Sanitize the model ID to ensure no double "models/" prefixes cause a 404
        raw_model = settings.embedding_model.replace("models/", "")
        self.model_id = f"models/{raw_model}"
        
        self.api_key = settings.gemini_api_key
        # text-embedding-004 outputs 768 dimensions natively. 
        # Ensure your settings and DB match this.
        self.dimension = settings.embedding_dimension 
        self.max_retries = 5 

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Returning zero embeddings.")
            return [[0.0] * self.dimension for _ in texts]
            
        # The URL requires the exact model string format: v1beta/models/text-embedding-004
        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_id}:batchEmbedContents?key={self.api_key}"
        headers = {
            "Content-Type": "application/json",
        }
        
        # Format the requests exactly how the Gemini API expects them
        requests = [
            {
                "model": self.model_id, 
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": self.dimension
            } 
            for text in texts
        ]
        payload = {"requests": requests}
        
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        raw = response.json()
                        embeddings = []
                        if "embeddings" in raw:
                            for emb_dict in raw["embeddings"]:
                                # Gemini returns a dict with 'values' array for the embedding
                                if "values" in emb_dict:
                                    embeddings.append(emb_dict["values"])
                        
                            # Pad with zero embeddings in case response is smaller than requested
                            while len(embeddings) < len(texts):
                                embeddings.append([0.0] * self.dimension)
                                
                            return embeddings
                            
                    elif response.status_code == 429:
                        # Explicitly handle rate limiting
                        logger.warning(f"Rate limited (429) on attempt {attempt}")
                        response.raise_for_status()

                    elif response.status_code == 400:
                        logger.error(f"Gemini 400 Bad Request: {response.text}")
                        response.raise_for_status()
                    else:
                        logger.error(f"Gemini Error {response.status_code}: {response.text}")
                        response.raise_for_status()

            except Exception as exc:
                # Exponential backoff with jitter (e.g., 2s, 4s, 8s, 16s + random milliseconds)
                wait = (2 ** attempt) + (random.randint(0, 1000) / 1000.0)
                logger.warning(
                    "Embedding failed on attempt %s/%s. Retrying in %.2fs: %s",
                    attempt,
                    self.max_retries,
                    wait,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(wait)

        logger.error("All embedding retries exhausted. Returning zero embedding.")
        return [[0.0] * self.dimension for _ in texts]