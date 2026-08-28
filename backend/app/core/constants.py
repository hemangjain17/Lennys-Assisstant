class ModelNames:
    EMBEDDING = "gemini-embedding-2"
    GEMINI = "gemini-3-flash-preview"
    OLLAMA = "gemma4:31b"
    RERANKER = "rerank-v3.5"

class GlobalVariables:
    EMBEDDING_DIMENSION = 768  # Output dimension for gemini-embedding-2
    EMBEDDING_VERSION = "v1"

    # Chunking Defaults
    CHUNK_TARGET_TOKENS = 350
    CHUNK_MIN_TOKENS = 200
    CHUNK_MAX_TOKENS = 450
    CHUNK_OVERLAP_TOKENS = 50

    # Retrieval Pipeline Defaults (Expanded for higher context density & coverage)
    VECTOR_TOP_K = 35
    
    LEXICAL_TOP_K = 35
    FUSION_TOP_K = 40
    RERANK_TOP_K = 20
    FINAL_CONTEXT_CHUNKS = 12
    SIMILARITY_THRESHOLD = 0.0
