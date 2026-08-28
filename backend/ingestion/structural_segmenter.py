import re
from typing import List, Dict, Optional

class StructuralSegmenter:
    """
    Segments podcast transcripts into logical blocks based on speaker turns.
    Detects patterns like:
    Speaker Name (00:00:00):
    (00:01:27):
    """
    def __init__(self):
        # Regex to match optional speaker name and mandatory timestamp in parens or brackets
        # E.g., "Brian Chesky (00:00:00):", "Lenny [01:32:14]:", "(00:01:27):", "[12:43]:"
        self.speaker_pattern = re.compile(r'^(?:(.*?)\s*)?[\(\[](\d{1,2}:\d{2}(?::\d{2})?)[\)\]]:\s*$')

    def segment(self, text: str) -> List[Dict]:
        lines = text.split('\n')
        segments = []
        current_speaker = None
        current_timestamp = None
        current_content = []

        def save_segment():
            if current_timestamp and current_content and ''.join(current_content).strip():
                content = '\n'.join(current_content).strip()
                segments.append({
                    "speaker": current_speaker,
                    "timestamp": current_timestamp,
                    "content": content
                })

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = self.speaker_pattern.match(line)
            if match:
                save_segment()
                
                speaker_match = match.group(1)
                timestamp_match = match.group(2)
                
                if speaker_match:
                    current_speaker = speaker_match.strip()
                current_timestamp = timestamp_match
                current_content = []
            else:
                current_content.append(line)

        save_segment()
        return segments
