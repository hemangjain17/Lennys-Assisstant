import argparse
import asyncio
import hashlib
import logging
import sys
from pathlib import Path

# Add the backend directory to the path so we can import modules.
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.core.config import settings
from ingestion.chunker import Chunker
from ingestion.embedder import Embedder
from ingestion.indexer import DatabaseNotInitializedError, Indexer, to_jsonable
from ingestion.parser import read_transcript
from ingestion.source_loader import get_transcript_files
from ingestion.structural_segmenter import StructuralSegmenter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def generate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def attach_chunk_metadata(chunks: list[dict], metadata: dict, filepath: str, content_hash: str) -> None:
    episode_metadata = to_jsonable(
        {
            **metadata,
            "source_path": str(filepath),
            "episode_content_hash": content_hash,
        }
    )

    for chunk in chunks:
        chunk["metadata"] = {
            "episode": episode_metadata,
            "chunk": {
                "speaker": chunk.get("speaker"),
                "start_timestamp": chunk.get("start_timestamp"),
                "end_timestamp": chunk.get("end_timestamp"),
            },
        }


async def async_main():
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast Transcripts into Supabase")
    parser.add_argument(
        "--source",
        type=str,
        default=settings.transcripts_repo_path,
        help="Path to the lennys-podcast-transcripts repo or its episodes directory",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip episodes whose content_hash already exists in DB",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk without saving to DB or calling the embedding API",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=settings.ingestion_batch_limit,
        help="Max number of episodes to process (0 = all)",
    )

    args = parser.parse_args()

    logger.info(f"Source: {args.source}")
    logger.info(
        f"Mode: {'Incremental' if args.incremental else 'Full'} | "
        f"Dry-run: {args.dry_run} | Limit: {args.limit or 'ALL'}"
    )
    logger.info(f"Embedding model: {settings.embedding_model} ({settings.embedding_dimension}-dim)")

    files = get_transcript_files(args.source)
    logger.info(f"Found {len(files)} transcript files.")

    if args.limit:
        files = files[: args.limit]
        logger.info(f"Limiting to first {args.limit} files.")

    segmenter = StructuralSegmenter()
    chunker = Chunker(
        target_tokens=settings.chunk_target_tokens,
        min_tokens=settings.chunk_min_tokens,
        max_tokens=settings.chunk_max_tokens,
        overlap=settings.chunk_overlap_tokens,
    )
    indexer = None if args.dry_run else Indexer()
    if indexer:
        try:
            indexer.verify_schema()
        except DatabaseNotInitializedError as exc:
            logger.error(str(exc))
            logger.error(
                "Open Supabase SQL Editor for this project and run the migration files in "
                "backend/database/migrations in filename order."
            )
            return
    embedder = None if args.dry_run else Embedder()

    success_count = 0
    fail_count = 0

    for i, filepath in enumerate(files):
        metadata, content = read_transcript(filepath)
        if not metadata or not content:
            logger.warning(f"[{i + 1}/{len(files)}] Skipping (bad parse): {filepath}")
            fail_count += 1
            continue

        title = metadata.get("title", "Unknown Title")
        content_hash = generate_hash(content)
        logger.info(f"[{i + 1}/{len(files)}] Processing: {title}")

        existing_episode_id = ""
        if indexer:
            existing_episode_id = indexer.find_episode_by_hash(content_hash)
            if args.incremental and existing_episode_id:
                logger.info("  -> Skipping unchanged episode (content_hash already indexed)")
                success_count += 1
                continue

        segments = segmenter.segment(content)
        logger.info(f"  -> {len(segments)} speaker segments")

        chunks = chunker.chunk_segments(segments, episode_id="dry-run")
        logger.info(f"  -> {len(chunks)} chunks")

        if args.dry_run:
            success_count += 1
            continue

        try:
            episode_id = indexer.index_episode(metadata, content_hash)
            if existing_episode_id:
                indexer.clear_episode_chunks(existing_episode_id)
            chunks = chunker.chunk_segments(segments, episode_id)
            attach_chunk_metadata(chunks, metadata, filepath, content_hash)
            logger.info(f"  -> {len(chunks)} chunks to embed")

            embeddings = []
            batch_size = settings.embedding_batch_size
            for j in range(0, len(chunks), batch_size):
                batch_texts = [c["content"] for c in chunks[j : j + batch_size]]
                batch_embs = await embedder.embed_batch(batch_texts)
                embeddings.extend(batch_embs)
                logger.info(f"     Embedded batch {j // batch_size + 1}/{-(-len(chunks) // batch_size)}")

            for chunk, emb in zip(chunks, embeddings):
                chunk["embedding"] = emb
                chunk["embedding_model"] = settings.embedding_model
                chunk["embedding_dimension"] = settings.embedding_dimension
                chunk["embedding_version"] = settings.embedding_version

            indexer.index_chunks(chunks)
            logger.info(f"  OK Indexed episode + {len(chunks)} chunks -> Supabase")
            success_count += 1

        except Exception as e:
            logger.error(f"  Failed to index '{title}': {e}")
            fail_count += 1

    logger.info("=" * 60)
    logger.info(f"Ingestion complete. Success: {success_count} | Failed: {fail_count}")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
