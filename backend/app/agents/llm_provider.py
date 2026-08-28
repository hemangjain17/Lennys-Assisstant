"""
Phase 5: LLM Provider Abstraction
Supports Gemini (primary) with graceful error handling.
Gemini API is used via direct httpx calls (no SDK dependency needed).
"""
import asyncio
import httpx
import json
import logging
from typing import AsyncIterator, List, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_STREAM_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:streamGenerateContent?alt=sse&key={key}"
)
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)


def _build_gemini_contents(messages: List[Dict]) -> List[Dict]:
    """Convert internal message list to Gemini API contents format."""
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    return contents


def _normalize_model_name(model_name: Optional[str]) -> str:
    """Pass model name directly to API, defaulting to settings if not provided."""
    if not model_name or model_name.strip() in ("", "default", "gemini"):
        return settings.gemini_model_name or "gemini-3-flash-preview"
    return model_name.strip()


class GeminiProvider:
    """Direct Gemini API provider via httpx (no google-generativeai SDK)."""

    def __init__(self, model_name: Optional[str] = None):
        self.api_key = settings.gemini_api_key
        self.model = _normalize_model_name(model_name or settings.gemini_model_name)

    async def generate(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Non-streaming generation. Returns full response string."""
        url = GEMINI_URL.format(model=self.model, key=self.api_key)
        body = {
            "contents": _build_gemini_contents(messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            data = r.json()

        try:
            candidate = data["candidates"][0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
            return ""
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Gemini response shape: {data}")
            return ""

    async def stream(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """SSE streaming generation. Yields text chunks as they arrive."""
        url = GEMINI_STREAM_URL.format(model=self.model, key=self.api_key)
        body = {
            "contents": _build_gemini_contents(messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        import json
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=body) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        raw = line[5:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            chunk = json.loads(raw)
                            text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                            yield text
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue


class OllamaCloudProvider:
    """Provider for Ollama Cloud & OpenAI-compatible endpoints."""

    def __init__(self, model_name: Optional[str] = None):
        self.api_key = settings.ollama_cloud_api_key
        self.base_url = (settings.ollama_cloud_base_url or "https://api.ollama.com/v1").rstrip("/")
        self.model = model_name or settings.ollama_cloud_model_name or "glm-5.3-flash:cloud"

    async def generate(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        body = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        if not self.api_key or not settings.ollama_cloud_base_url:
            logger.warning(f"Ollama Cloud not fully configured, falling back to Gemini for model {self.model}")
            fallback = GeminiProvider(model_name="gemini-3-flash-preview")
            async for chunk in fallback.stream(messages, system_prompt, temperature, max_tokens):
                yield chunk
            return

        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        body = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=body) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            raw = line[5:].strip()
                            if raw == "[DONE]":
                                break
                            try:
                                chunk = json.loads(raw)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield delta
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"Ollama Cloud stream failed: {e}. Falling back to Gemini.")
            fallback = GeminiProvider(model_name="gemini-3-flash-preview")
            async for chunk in fallback.stream(messages, system_prompt, temperature, max_tokens):
                yield chunk


class OllamaLocalProvider:
    """Provider for Local Ollama installations (e.g., llama3.1 on localhost:11434)."""

    def __init__(self, model_name: Optional[str] = None):
        self.base_url = (settings.ollama_local_base_url or "http://localhost:11434").rstrip("/")
        self.model = model_name or settings.ollama_local_model_name or "llama3.1"

    async def _ensure_model(self) -> None:
        """
        Verifies if the requested model exists. If not:
        - Resolves to a substring match (e.g. 'llama3.1' -> 'llama3.1:8b')
        - If no match, starts pulling the model in the background and raises an exception so fallback Gemini is used.
        """
        try:
            # Fast check: connect & read timeout of 2.0 seconds to prevent hanging if local Ollama is offline
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                if r.status_code != 200:
                    return
                models = [m["name"] for m in r.json().get("models", [])]
                
            # 1. Exact Match
            if self.model in models:
                return
                
            # 2. Substring / Tag Resolution (e.g. 'llama3.1' matches 'llama3.1:8b' or 'llama3.1:latest')
            for m in models:
                if m.startswith(self.model + ":") or (self.model in m):
                    logger.info(f"Ollama Local: resolved '{self.model}' to existing model '{m}'")
                    self.model = m
                    return
            
            # 3. Model not installed. Trigger a background pull and raise exception to trigger immediate Gemini fallback
            logger.warning(f"Ollama Local: model '{self.model}' not found. Starting background pull...")
            # Fire and forget pull request
            asyncio.create_task(self._pull_model_background())
            raise ValueError(f"Model '{self.model}' not found locally. Background pull initiated.")
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            logger.warning(f"Failed to check/resolve Ollama model: {e}")

    async def _pull_model_background(self) -> None:
        """Background coroutine to pull a missing Ollama model."""
        url = f"{self.base_url}/api/pull"
        logger.info(f"Ollama Background Pull started for '{self.model}'")
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                r = await client.post(url, json={"name": self.model, "stream": False})
                if r.status_code == 200:
                    logger.info(f"Ollama Background Pull successful for '{self.model}'")
                else:
                    logger.error(f"Ollama Background Pull failed for '{self.model}': {r.text}")
        except Exception as e:
            logger.error(f"Ollama Background Pull exception: {e}")

    async def generate(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        try:
            await self._ensure_model()
            url = f"{self.base_url}/api/chat"
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.extend(messages)

            body = {
                "model": self.model,
                "messages": formatted_messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                },
                "stream": False
            }

            # Fail fast within 8.0 seconds total if local Ollama hangs or is unresponsive (e.g. while loading model to VRAM)
            timeout_config = httpx.Timeout(8.0, connect=2.0, read=8.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                r = await client.post(url, json=body)
                r.raise_for_status()
                data = r.json()
                return data["message"]["content"]
        except Exception as e:
            logger.error(f"Local Ollama generate failed: {e}. Falling back to Gemini.")
            fallback = GeminiProvider(model_name="gemini-3-flash-preview")
            return await fallback.generate(messages, system_prompt, temperature, max_tokens)

    async def stream(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        try:
            await self._ensure_model()
            url = f"{self.base_url}/api/chat"
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.extend(messages)

            body = {
                "model": self.model,
                "messages": formatted_messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                },
                "stream": True
            }

            # Fail fast within 8.0 seconds total if local Ollama hangs on initiating stream
            timeout_config = httpx.Timeout(8.0, connect=2.0, read=8.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                async with client.stream("POST", url, json=body) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            delta = chunk["message"].get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as e:
            logger.error(f"Local Ollama stream failed: {e}. Falling back to Gemini.")
            fallback = GeminiProvider(model_name="gemini-3-flash-preview")
            async for chunk in fallback.stream(messages, system_prompt, temperature, max_tokens):
                yield chunk


def get_llm_provider(model_name: Optional[str] = None):
    model = (model_name or settings.gemini_model_name).lower()
    if "local" in model or "11434" in model:
        # Reformat model name to strip local identifier if present
        clean_model = model.replace("-local", "").replace("(local)", "").strip()
        return OllamaLocalProvider(model_name=clean_model if clean_model else None)
    if "glm" in model or "ollama" in model or "llama" in model or "cloud" in model:
        return OllamaCloudProvider(model_name=model_name)
    return GeminiProvider(model_name=model_name)
