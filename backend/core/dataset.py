"""Read indexed baselines; reject unindexed IDs and paths outside the dataset."""
import json
import re
from pathlib import Path
from backend.config import DATASET_DIR
from backend.models.schemas import Alignment


def safe_path(relative: str, root: Path = DATASET_DIR) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("Dataset path escapes the dataset directory")
    return candidate


def list_baselines(root: Path = DATASET_DIR) -> list[dict]:
    path = root / "metadata.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["speeches"]


def get_baseline(speech_id: str, root: Path = DATASET_DIR):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", speech_id):
        raise ValueError("Invalid baseline ID")
    entry = next((s for s in list_baselines(root) if s["id"] == speech_id), None)
    if entry is None:
        raise ValueError("Baseline not found; build or import a dataset first")
    folder = safe_path(entry["path"], root)
    transcript = (folder / "transcript.txt").read_text(encoding="utf-8").strip()
    alignment = Alignment.model_validate_json((folder / "ideal" / "alignment.json").read_text(encoding="utf-8"))
    return entry, folder, transcript, alignment
