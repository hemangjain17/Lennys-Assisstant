# Full Implementation of the Lenny Growth Assistant

The project scope has been significantly updated from a scaffolding task to a **full, working implementation**. This implementation plan outlines how we will build out the complete production-oriented architecture, including the Next.js frontend, FastAPI backend, Supabase database, RAG pipeline, and Agent integrations.

## User Review Required

This is a massive project. I have broken the implementation down into several major phases. Because of the size and complexity, I propose we tackle this systematically, verifying each major component before moving on.

Please review the proposed approach and phases. Once approved, I will begin implementing Phase 1 and 2.

## Open Questions

1. **API Keys and Credentials**: To actually build and test this, we will need access to various API keys (Supabase, Gemini API, etc.). Should I rely strictly on mocked providers for now, or will you be providing environment variables for me to test against real infrastructure?
2. **Existing Dependencies**: The prompt mentions "inspect existing project/dependencies/configuration." We previously found the directories were empty. Should I initialize standard boilerplates (`npx create-next-app`, `poetry init`, etc.) now, or stick to the exact file structures we just scaffolded and manually populate them?
3. **Pi Coding Agent integration**: The prompt mentions a `pi-agent` directory and SDK integration. Since we didn't scaffold a `pi-agent` folder earlier (it was a backend adapter in the previous prompt), should I create this new standalone directory as specified in the updated instructions?

## Proposed Implementation Phases

### Phase 1: Project Initialization & Configuration

- Initialize Next.js in the `frontend/` directory with Tailwind CSS and TypeScript.
- Initialize Python environment in the `backend/` directory with `requirements.txt` (FastAPI, Pydantic, Supabase, pgvector, httpx, etc.).
- Establish the `docker-compose.yml` for local execution.
- Create the `.env.example` configurations.
- Set up logging, error handling, and structured telemetry in the backend.

### Phase 2: Database & Models (Supabase)

- Create Supabase migrations for all required tables (`episodes`, `transcript_chunks`, `sessions`, `messages`, `artifacts`, etc.).
- Enable the `pgvector` extension and create the `match_transcript_chunks` RPC function.
- Implement the Supabase client wrapper and repositories (`app/db/repositories/`) to handle data access securely.

### Phase 3: Ingestion Pipeline

- Implement the transcript parsing logic (`ingestion/parser.py`).
- Build the structural chunking logic (`ingestion/structural_segmenter.py`, `chunker.py`) with configurable token limits.
- Integrate the cloud embedding abstraction (`ingestion/embedder.py`).
- Implement the incremental sync logic based on content hashes (`ingestion/sync.py`).

### Phase 4: Retrieval Pipeline (RAG)

- Implement hybrid retrieval combining pgvector dense search and PostgreSQL full-text lexical search.
- Implement Reciprocal Rank Fusion (RRF) and Maximum Marginal Relevance (MMR) deduplication.
- Implement conditional context expansion to pull parent/neighbor chunks.
- Build the adaptive retrieval policies (Simple, Complex, Multi-part).

### Phase 5: LLM & Agent Routing

- Implement the `LLMProvider` abstraction supporting both Gemini and Ollama Cloud.
- Implement the Pi Agent Adapter and orchestration loop with bounded iterations.
- Implement query classification, query rewriting for follow-ups, and query decomposition.
- Build the Ship30 and Artifact generation skills.

### Phase 6: API Layer

- Connect the core logic to FastAPI routes (`sessions`, `chat`, `artifacts`, `evaluations`).
- Implement SSE (Server-Sent Events) streaming for the chat endpoint.
- Implement the health and readiness checks.

### Phase 7: Frontend UI (Next.js)

- Build the chat interface (sidebar, message bubbles, composer).
- Implement progressive SSE stream parsing.
- Build the Artifact Viewer with a secure HTML iframe sandbox and Markdown renderer.
- Add model toggling and citation components.

### Phase 8: Testing, Security & Docs

- Implement prompt injection defenses and strict schema validations.
- Write unit tests, API tests, and mock provider integrations.
- Complete the final README and architecture documentation.

## Verification Plan

After each phase, I will run relevant tests (using mocks if necessary) and provide a walkthrough of the components built. At the end of the project, I will provide the required deployment commands and a fully functional end-to-end smoke test simulation.
