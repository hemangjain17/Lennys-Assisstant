from typing import List, Dict
import hashlib
from app.retrieval.source_mapper import parse_timestamp

def count_tokens(text: str) -> int:
    # MVP token estimation (1 token ~= 4 chars)
    return len(text) // 4

def generate_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

class Chunker:
    def __init__(self, target_tokens: int = 700, min_tokens: int = 400, max_tokens: int = 900, overlap: int = 80):
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap = overlap

    def chunk_segments(self, segments: List[Dict], episode_id: str) -> List[Dict]:
        chunks = []
        current_chunk_content = []
        current_tokens = 0
        chunk_index = 0
        start_timestamp = None
        end_timestamp = None
        current_speakers = []

        def format_segment(seg: Dict) -> str:
            speaker = seg.get("speaker") or "Unknown speaker"
            timestamp = seg.get("timestamp") or "unknown"
            return f"{speaker} ({timestamp}):\n{seg['content']}"

        def add_speaker(speaker: str):
            if speaker and speaker not in current_speakers:
                current_speakers.append(speaker)

        def save_chunk(content_str: str, speakers: List[str], start_ts: str, end_ts: str, parent_id: str = None):
            nonlocal chunk_index
            start_ts_sec = parse_timestamp(start_ts)
            chunks.append({
                "chunk_index": chunk_index,
                "episode_id": episode_id,
                "parent_chunk_id": parent_id,
                "content": content_str,
                "speaker": ", ".join(speakers) if speakers else None,
                "start_timestamp": start_ts,
                "start_timestamp_seconds": start_ts_sec,
                "end_timestamp": end_ts,
                "token_count": count_tokens(content_str),
                "content_hash": generate_hash(content_str)
            })
            chunk_index += 1

        for seg in segments:
            seg_tokens = count_tokens(seg['content'])
            
            # If segment itself is too large, split it into sliding windows
            if seg_tokens > self.max_tokens:
                # Flush existing buffer
                if current_chunk_content:
                    content_str = "\n".join(current_chunk_content)
                    save_chunk(content_str, current_speakers, start_timestamp, end_timestamp)
                    current_chunk_content = []
                    current_tokens = 0
                    current_speakers = []
                    start_timestamp = None
                    end_timestamp = None
                
                # Split large segment (simplified sliding window by characters)
                text = format_segment(seg)
                step = self.target_tokens * 4
                overlap_chars = self.overlap * 4
                
                # Save parent chunk
                parent_id = None # In a real implementation we would generate a UUID here and save it to the DB first
                
                start = 0
                while start < len(text):
                    end = min(start + step, len(text))
                    window_text = text[start:end]
                    save_chunk(window_text, [seg.get('speaker')] if seg.get('speaker') else [], seg['timestamp'], seg['timestamp'], parent_id=parent_id)
                    start += step - overlap_chars
                continue

            # If adding this segment exceeds target, flush buffer
            if current_tokens + seg_tokens > self.target_tokens and current_chunk_content:
                content_str = "\n".join(current_chunk_content)
                save_chunk(content_str, current_speakers, start_timestamp, end_timestamp)
                
                # Keep the last segment for overlap if needed (simplified: just reset)
                current_chunk_content = []
                current_tokens = 0
                start_timestamp = None
                end_timestamp = None
                current_speakers = []

            if not current_chunk_content:
                start_timestamp = seg['timestamp']

            current_chunk_content.append(format_segment(seg))
            current_tokens += count_tokens(current_chunk_content[-1])
            end_timestamp = seg['timestamp']
            add_speaker(seg.get('speaker'))

        if current_chunk_content:
            content_str = "\n".join(current_chunk_content)
            save_chunk(content_str, current_speakers, start_timestamp, end_timestamp)

        return chunks
