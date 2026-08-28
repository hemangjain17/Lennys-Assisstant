# System Architecture & Topology: Lenny Growth Assistant

---

## 1. SYSTEM TOPOLOGY

```
                         USER
                           │
                           ▼
                 [Next.js UI Frontend]
                           │
                    REST / SSE Stream
                           │
                           ▼
                [FastAPI Backend Server]
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
   [Ollama Local]                       [Gemini API] (Cloud)
  (llama3.1 server)                          │
         │                                   ▼
         │                             [Supabase DB] (Postgres)
         │                                   │
         └─────────────────┬─────────────────┘
                           │
                           ▼
                    Grounded Context
```

---

## 2. DATABASE SCHEMA (`Supabase / PostgreSQL`)

### 2.1 Table: `episodes`
*   `id` UUID PRIMARY KEY
*   `guest` TEXT, `title` TEXT, `description` TEXT
*   `youtube_url` TEXT, `video_id` TEXT, `content_hash` TEXT

### 2.2 Table: `transcript_chunks`
*   `id` UUID PRIMARY KEY
*   `episode_id` REFERENCES `episodes`
*   `chunk_index` INTEGER, `content` TEXT
*   `embedding` `vector(768)` (GIN & HNSW Cosine Index)
*   `start_timestamp` TEXT, `start_timestamp_seconds` INTEGER

### 2.3 Table: `artifacts`
*   `id` UUID PRIMARY KEY, `session_id` UUID, `message_id` UUID
*   `type` TEXT (markdown/html), `title` TEXT, `content` TEXT
*   `version` INTEGER, `metadata` JSONB

---

## 3. API ENDPOINTS

*   `POST /api/v1/sessions`: Create new session.
*   `GET /api/v1/sessions`: List past sessions (metadata & titles).
*   `GET /api/v1/sessions/{id}/messages`: Fetch full message history.
*   `POST /api/v1/chat`: Streaming SSE endpoint for conversational RAG queries and artifact rendering.

---

## 4. SECURITY BOUNDARIES
*   **Database RLS**: Suppress anonymous writes; only Service Role or authenticated writes enabled.
*   **HTML Artifact Sandbox**: Rendered inside an `<iframe>` with strict sandboxing:
    ```html
    <iframe sandbox="allow-scripts" src="..." />
    ```
    Excludes `allow-same-origin` to isolate the page from the parent DOM, localStorage, and API cookies.

---

## 5. PROMPT SYSTEM ARCHITECTURE

The prompt system has been completely audited, optimized, and redesigned into a highly secure, modular, and grounded architecture.

### 5.1 Pipeline Topology
The flow for processing any user query is:
```
 USER QUERY
     ↓
 1. INTENT CLASSIFICATION (`query_classifier.md`)
     ↓ 
 2. STANDALONE QUERY REWRITE (`query_rewriter.md` - if follow-up)
     ↓
 3. QUERY DECOMPOSITION / MULTI-QUERY EXPANSION (`query_expander.md` - if complex query)
     ↓
 4. PARALLEL RAG RETRIEVAL & VECTOR SEARCH
     ↓
 5. ANSWER GENERATION WITH INJECTION-RESISTANT CONTEXT (`system.md`)
     ↓
 6. GROUNDING & CITATION VERIFICATION (`grounding_verifier.md`)
     ↓
 FINAL RESPONSE & METADATA DB LOGGING
```

### 5.2 Prompt Inventory & Modules
The prompts are centralized under `backend/app/agents/prompts/`:
*   `system.md`: The core developer system prompt defining grounding constraints, guest-specific attribution rules, formatting templates, and citation instructions.
*   `query_classifier.md`: Analyzes user query and conversation history to produce structured JSON routing signals (`type`, `intent`, `requires_rag`, `is_follow_up`, `requires_multi_query`, `requires_citations`).
*   `query_rewriter.md`: Conversational follow-up rewriter. Resolves references and pronouns using previous history to create clear search queries.
*   `query_expander.md`: Breaks down complex synthesis questions into 2-4 distinct subqueries for parallel database retrieval.
*   `grounding_verifier.md`: Audits the generated response against source transcripts to detect and flag any unsupported claims or hallucinations.
*   `artifact.md` / `ship30.md`: Specialty style prompts for generating formatted structures and essays.

### 5.3 Prompt Injection Defense & Sandwich Prompting
The retrieved transcripts are treated as untrusted reference data, enclosed inside strong `<retrieved_lenny_transcripts>` XML tags. Strict instructions are provided before and reinforced after context blocks (sandwich prompting) to prevent instruction-override or system prompt extraction.

### 5.4 Grounding Policy
The transcripts are the absolute source of truth. Factual claims without evidence are strictly rejected or result in transparent failure responses: `"I couldn't find enough relevant discussion in the available Lenny Podcast transcripts to answer that confidently."`
