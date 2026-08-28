# Agent Coding Transcript: Resolution of Key Pipeline Defects

This document records the exact transcripts, log warnings, failures, and resolution plans executed during the construction of the **Lenny Growth Assistant**.

---

## 1. TRANSACTION: RE-VECTORING AND DATABASE MISMATCHES

### 1.1 The Failure:
During the ingestion setup, calling `python -m ingestion.sync` failed with the following error:
```
[ERROR] Failed to index 'When to invest in new acquisition channels | Adam Grenier (Uber, MasterClass)': 
{'message': 'expected 1024 dimensions, not 3072', 'code': '22000', 'hint': None, 'details': None}
```

### 1.2 Root Cause Analysis:
The Supabase table `transcript_chunks` and pg_vector indices were scaffolded to expect `1024` dimensions (from the old Qwen embedding model). However, the active model selected (`gemini-embedding-001`) emitted `3072` dimensions, causing the Postgres database to reject the inserts.

### 1.3 Correction Plan:
- Updated the SQL migrations (`003_chunks.sql` and `010_vector_search.sql`) to expect `768` dimensions.
- Switched the Gemini model to `gemini-embedding-2` with `outputDimensionality: 768`.
- Truncated the old tables and applied the migrations successfully.

---

## 2. TRANSACTION: SUPABASE REST TEXT_SEARCH ATTRIBUTE ERROR

### 2.1 The Failure:
```
[ERROR] app.retrieval.lexical_search — Lexical search failed: 'SyncQueryRequestBuilder' object has no attribute 'limit'
```

### 2.2 Root Cause Analysis:
In the `supabase-py` PostgREST library, calling `.text_search("fts", query)` transforms the request builder into a filter builder where `.limit()` can no longer be appended directly.

### 2.3 Correction Plan:
Reordered the method chain in `lexical_search.py` so `.limit(top_k)` is attached to the `.select()` statement **prior** to running `text_search`.

---

## 3. TRANSACTION: ARTIFACT DATABASE PERSISTENCE MISMATCH

### 3.1 The Failure:
```
[ERROR] app.api.chat — Failed to save artifact to DB: {'message': 'column artifacts.version does not exist', 'code': '42703', 'hint': None, 'details': None}
```

### 3.2 Root Cause Analysis:
The `artifacts` table was missing the `version` and `metadata` columns.

### 3.3 Correction Plan:
- Executed PostgreSQL schema migrations to add `version` and `metadata` to `artifacts`.
- Implemented a robust try/except fallback block inside `_save_artifact_if_present()` so it automatically degrades to inserting standard fields if schema discrepancies occur.
