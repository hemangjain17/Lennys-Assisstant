from pathlib import Path
from typing import List

def get_transcript_files(base_repo_path: str) -> List[str]:
    """
    Finds all transcript.md files in the lennys-podcast-transcripts repository.
    Accepts the repository root, episodes/ directory, or one episode directory.
    """
    source = Path(base_repo_path).expanduser().resolve()
    if (source / "transcript.md").exists():
        return [str(source / "transcript.md")]

    episodes_dir = source if source.name == "episodes" else source / "episodes"
    if not episodes_dir.exists():
        print(f"Warning: Episodes directory {episodes_dir} does not exist.")
        return []

    return sorted(str(path) for path in episodes_dir.rglob("transcript.md"))
