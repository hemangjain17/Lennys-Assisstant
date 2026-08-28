import yaml
import re
from typing import Tuple, Dict, Optional
from app.retrieval.source_mapper import extract_youtube_video_id, parse_youtube_url

FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)(.*)\Z", re.DOTALL)

def read_transcript(filepath: str) -> Tuple[Optional[Dict], str]:
    """
    Reads a transcript file, splits the frontmatter from the content,
    and returns the metadata dict and the transcript string.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        match = FRONTMATTER_PATTERN.match(content)
        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            transcript = match.group(2)

            # Robust YouTube URL & Video ID extraction
            raw_yt = frontmatter.get("youtube_url") or frontmatter.get("video_id")
            parsed_yt = parse_youtube_url(raw_yt)
            if parsed_yt:
                frontmatter["youtube_url"] = parsed_yt["canonical_url"]
                frontmatter["video_id"] = parsed_yt["video_id"]
            elif frontmatter.get("youtube_url"):
                vid = extract_youtube_video_id(frontmatter["youtube_url"])
                if vid:
                    frontmatter["video_id"] = vid
                    frontmatter["youtube_url"] = f"https://www.youtube.com/watch?v={vid}"

            return frontmatter, transcript.strip()
        
        # If no frontmatter, return just the content
        return None, content.strip()
    except Exception as e:
        print(f"Error parsing file {filepath}: {e}")
        return None, ""
