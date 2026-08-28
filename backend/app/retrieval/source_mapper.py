"""
Source & Citation Mapping Utility
Extracts YouTube URLs, parses timestamps, builds canonical YouTube timestamp URLs,
and creates structured citation objects with deterministic fallback logic.
"""
import re
import urllib.parse
from typing import Dict, List, Optional, Union

YOUTUBE_ID_PATTERN = re.compile(
    r'(?:youtube\.com/(?:watch\?.*v=|embed/|v/)|youtu\.be/)([\w-]{11})',
    re.IGNORECASE
)
RAW_ID_PATTERN = re.compile(r'^[\w-]{11}$')


def parse_timestamp(timestamp_val: Optional[Union[str, int, float]]) -> Optional[int]:
    """
    Parses timestamps in formats like:
      - "00:12:43", "01:32:14", "12:43", "1:32:14", "[00:12:43]", "(01:32:14)"
      - Integer or float seconds (e.g. 763, 5534.0)
    Returns total seconds as integer, or None if invalid.
    """
    if timestamp_val is None:
        return None

    if isinstance(timestamp_val, (int, float)):
        if timestamp_val < 0:
            return None
        return int(timestamp_val)

    ts_str = str(timestamp_val).strip()
    if not ts_str:
        return None

    # Strip surrounding brackets/parentheses if present
    ts_str = ts_str.strip("[]()")

    # Handle pure digit string (e.g., "763")
    if ts_str.isdigit():
        val = int(ts_str)
        return val if val >= 0 else None

    # Match time format HH:MM:SS, H:MM:SS, MM:SS, M:SS
    parts = ts_str.split(":")
    if not (2 <= len(parts) <= 3):
        return None

    try:
        parts_int = [int(p) for p in parts]
        if any(p < 0 for p in parts_int):
            return None

        if len(parts_int) == 3:
            h, m, s = parts_int
            if m >= 60 or s >= 60:
                return None
            return h * 3600 + m * 60 + s
        else:
            m, s = parts_int
            if s >= 60:
                return None
            return m * 60 + s
    except (ValueError, TypeError):
        return None


def extract_youtube_video_id(url_or_id: Optional[str]) -> Optional[str]:
    """
    Extracts the 11-character YouTube video ID from various YouTube URL forms or raw ID string.
    Supports:
      - https://www.youtube.com/watch?v=KPxTekxQjzc
      - https://youtu.be/KPxTekxQjzc
      - https://www.youtube.com/watch?v=KPxTekxQjzc&t=123s
      - https://www.youtube.com/embed/KPxTekxQjzc
      - Raw 11-character video ID strings
    Returns the 11-character video ID or None.
    """
    if not url_or_id:
        return None

    val = str(url_or_id).strip()
    if not val:
        return None

    # Direct 11-char video ID check
    if RAW_ID_PATTERN.match(val):
        return val

    # Match in URL
    match = YOUTUBE_ID_PATTERN.search(val)
    if match:
        return match.group(1)

    return None


def parse_youtube_url(url_or_id: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Normalizes a YouTube URL/ID into a dict containing:
      - 'video_id': 'KPxTekxQjzc'
      - 'canonical_url': 'https://www.youtube.com/watch?v=KPxTekxQjzc'
    Returns None if not a valid YouTube source.
    """
    video_id = extract_youtube_video_id(url_or_id)
    if not video_id:
        return None

    return {
        "video_id": video_id,
        "canonical_url": f"https://www.youtube.com/watch?v={video_id}",
    }


def build_youtube_timestamp_url(
    url_or_id: Optional[str],
    timestamp_val: Optional[Union[str, int, float]]
) -> str:
    """
    Generates a deterministic YouTube timestamp URL.
    Examples:
      - ("KPxTekxQjzc", "01:32:14") -> "https://www.youtube.com/watch?v=KPxTekxQjzc&t=5534s"
      - ("KPxTekxQjzc", 763) -> "https://www.youtube.com/watch?v=KPxTekxQjzc&t=763s"
      - ("KPxTekxQjzc", None) -> "https://www.youtube.com/watch?v=KPxTekxQjzc"
    Falls back gracefully if YouTube URL / video ID or timestamp is unavailable.
    """
    parsed = parse_youtube_url(url_or_id)
    seconds = parse_timestamp(timestamp_val)

    if parsed:
        canonical_url = parsed["canonical_url"]
        if seconds is not None:
            return f"{canonical_url}&t={seconds}s"
        return canonical_url

    # Non-YouTube fallback URL
    if url_or_id:
        return str(url_or_id)

    return ""


def format_display_timestamp(timestamp_val: Optional[Union[str, int, float]]) -> str:
    """
    Formats timestamp for display e.g. "▶ 01:32:14" or "▶ 12:43".
    """
    seconds = parse_timestamp(timestamp_val)
    if seconds is None:
        return ""

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"▶ {h:02d}:{m:02d}:{s:02d}"
    return f"▶ {m:02d}:{s:02d}"


def build_citation_source(chunk: Dict) -> Dict:
    """
    Constructs a structured citation source dict with strict fallback logic:
      1. YouTube URL + valid timestamp -> Timestamp citation with &t=...s
      2. YouTube URL but no timestamp -> Canonical video URL
      3. Episode metadata available but no YouTube URL -> Episode/Source URL
      4. Only guest/title available -> Plain citation without URL
    """
    episode = chunk.get("episode", {})
    metadata = chunk.get("metadata", {})
    ep_metadata = metadata.get("episode", {}) if isinstance(metadata.get("episode"), dict) else {}

    guest = episode.get("guest") or ep_metadata.get("guest") or chunk.get("speaker") or "Lenny's Podcast"
    title = episode.get("title") or ep_metadata.get("title") or "Episode"
    company = ep_metadata.get("company") or ""

    raw_yt = (
        episode.get("youtube_url")
        or episode.get("video_id")
        or ep_metadata.get("youtube_url")
        or ep_metadata.get("video_id")
    )
    raw_source = episode.get("source_url") or ep_metadata.get("source_url") or ""
    raw_ts = (
        chunk.get("start_timestamp")
        or (chunk.get("metadata", {}).get("chunk", {}).get("start_timestamp") if isinstance(chunk.get("metadata"), dict) else None)
    )

    seconds = parse_timestamp(raw_ts)
    yt_info = parse_youtube_url(raw_yt)

    # Priority 1: YouTube + Timestamp
    if yt_info and seconds is not None:
        url = f"{yt_info['canonical_url']}&t={seconds}s"
        display_ts = format_display_timestamp(raw_ts)
        citation_type = "youtube_timestamp"
    # Priority 2: YouTube, no timestamp
    elif yt_info:
        url = yt_info["canonical_url"]
        display_ts = ""
        citation_type = "youtube_video"
    # Priority 3: Non-YouTube Source URL
    elif raw_source:
        url = raw_source
        display_ts = format_display_timestamp(raw_ts) if seconds is not None else ""
        citation_type = "external_url"
    # Priority 4: Plain metadata citation
    else:
        url = ""
        display_ts = format_display_timestamp(raw_ts) if seconds is not None else ""
        citation_type = "plain"

    video_id = yt_info["video_id"] if yt_info else ""

    return {
        "id": str(chunk.get("id", "")),
        "guest": guest,
        "title": title,
        "company": company,
        "youtube_url": yt_info["canonical_url"] if yt_info else "",
        "youtube_video_id": video_id,
        "start_timestamp": str(raw_ts or ""),
        "timestamp_seconds": seconds,
        "display_timestamp": display_ts,
        "url": url,
        "citation_type": citation_type,
        "avatarUrl": guest[:2].upper() if guest else "LP",
    }


def map_chunks_to_sources(chunks: List[Dict]) -> List[Dict]:
    """
    Maps a list of retrieved chunks into unique, clean citation sources.
    """
    sources = []
    seen = set()

    for chunk in chunks:
        citation = build_citation_source(chunk)
        key = (citation["guest"], citation["title"], citation["url"])
        if key not in seen:
            seen.add(key)
            sources.append(citation)

    return sources
