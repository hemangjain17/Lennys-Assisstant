"""
Phase 6: API Layer — Pydantic models for request/response contracts.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


# ── Session models ────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── Chat models ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=4000)
    model: Optional[str] = "gemini"           # gemini | ollama
    filter_guest: Optional[str] = None        # e.g. "Brian Chesky"
    filter_episode_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    model_provider: Optional[str]
    model_name: Optional[str]
    created_at: datetime


# ── Artifact models ───────────────────────────────────────────────────────────

class ArtifactCreate(BaseModel):
    session_id: str
    message_id: str
    type: str = Field(..., pattern="^(markdown|html)$")
    title: Optional[str] = None
    content: str
    language: Optional[str] = None

class ArtifactResponse(BaseModel):
    id: str
    session_id: str
    message_id: str
    type: str
    title: Optional[str]
    content: str
    language: Optional[str]
    created_at: datetime


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    environment: str
