# Product Requirement Document (PRD): Lenny Growth Assistant

---

## 1. USER PERSONA & GOALS
*   **Target User**: Product Managers, Growth Marketers, and Startup Founders.
*   **User Goals**: Access highly specific, reliable, and historically accurate product/growth insights shared by domain experts on Lenny's Podcast.
*   **Success Metric**: Retrieval precision ($> 95\%$), zero hallucinations, and clickable YouTube timestamp citations.

---

## 2. PROBLEM STATEMENT
*   Podcast transcripts are long, unstructured, and contain conversational noise.
*   Conventional generic RAG architectures face "lost in the middle" context limitations, retrieve redundant quotes, and often fail to provide exact citation timestamp references.

---

## 3. SCOPE & BOUNDARIES
*   **In-Scope (V1)**: Hybrid dense/lexical search, reciprocal rank fusion (RRF), cross-encoder reranking, smart context expansion, MMR diversity filtering, inline timestamp citations, and custom artifact generation (essays, tables).
*   **Out-of-Scope (V1)**: Native user auth, multi-tenant billing, audio-to-text transcript processing (pre-processed transcripts only).

---

## 4. SYSTEM FLOWS & CRITERIA
*   **User Question Flow**: User asks a query $\rightarrow$ intent classification determines flow $\rightarrow$ hybrid RAG executes $\rightarrow$ cross-episode synthesis streamed token-by-token.
*   **Artifact Flow**: Artifact requested $\rightarrow$ skill routed $\rightarrow$ streams structured `<artifact>` markdown into live side panel $\rightarrow$ stored in DB on done.

---

## 5. RISKS & MITIGATION
*   *Rate Limits*: Handled with exponential backoff and jitter.
*   *Database Connection Latency*: Solved by utilizing HNSW pgvector indices for millisecond-level cosine similarity lookups.
