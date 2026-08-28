from app.db.client import get_supabase_client
from typing import Any, Dict, List
from datetime import date, datetime


class DatabaseNotInitializedError(RuntimeError):
    pass


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    return value

class Indexer:
    def __init__(self):
        self.client = get_supabase_client()

    def verify_schema(self) -> None:
        try:
            self.client.table("episodes").select("id").limit(1).execute()
            self.client.table("transcript_chunks").select("id").limit(1).execute()
        except Exception as exc:
            message = str(exc)
            if "PGRST205" in message or "schema cache" in message or "Could not find the table" in message:
                raise DatabaseNotInitializedError(
                    "Supabase tables are missing. Run the SQL files in "
                    "backend/database/migrations against the Supabase project, "
                    "then rerun ingestion."
                ) from exc
            raise

    def find_episode_by_hash(self, content_hash: str) -> str:
        try:
            response = (
                self.client.table("episodes")
                .select("id")
                .eq("content_hash", content_hash)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            message = str(exc)
            if "PGRST205" in message or "schema cache" in message or "Could not find the table" in message:
                raise DatabaseNotInitializedError(
                    "Supabase table public.episodes is missing. Run backend/database/migrations first."
                ) from exc
            raise
        if response.data:
            return response.data[0]["id"]
        return ""

    def clear_episode_chunks(self, episode_id: str) -> None:
        self.client.table("transcript_chunks").delete().eq("episode_id", episode_id).execute()

    def index_episode(self, metadata: Dict, content_hash: str) -> str:
        """
        Inserts or updates an episode and returns its ID.
        """
        existing_id = self.find_episode_by_hash(content_hash)
        if existing_id:
            return existing_id

        data = {
            "title": metadata.get("title", "Unknown"),
            "guest": metadata.get("guest"),
            "description": metadata.get("description"),
            "youtube_url": metadata.get("youtube_url"),
            "video_id": metadata.get("video_id"),
            "publish_date": to_jsonable(metadata.get("publish_date")),
            "duration": metadata.get("duration"),
            "content_hash": content_hash,
            "source_url": metadata.get("source_url") or metadata.get("youtube_url"),
        }
        
        response = self.client.table("episodes").insert(data).execute()
        if response.data:
            return response.data[0]['id']
        raise Exception(f"Failed to index episode: {metadata.get('title')}")

    def index_chunks(self, chunks: List[Dict]):
        """
        Batch inserts chunks.
        """
        if not chunks:
            return
            
        # Supabase allows batch inserts up to a certain size
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            self.client.table("transcript_chunks").insert(batch).execute()
