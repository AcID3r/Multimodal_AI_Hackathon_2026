"""Integrity checks. --submission rejects fixtures and unreviewed real recordings."""
import argparse
import hashlib
import json
from backend.config import SAMPLE_RATE
from backend.core.audio import load_audio
from backend.core.alignment import validate_alignment
from backend.core.dataset import list_baselines, safe_path
from backend.models.schemas import Alignment


def validate(submission: bool = False):
    speeches = list_baselines()
    if not speeches or len({s["id"] for s in speeches}) != len(speeches):
        raise ValueError("Dataset is empty or IDs are duplicated")
    real = [s for s in speeches if s["kind"] == "real_speech" and s["human_reviewed"]]
    if submission and len(real) < 5:
        raise ValueError(f"Submission needs >=5 reviewed real speeches; currently {len(real)}")
    checked = 0
    for entry in speeches:
        folder = safe_path(entry["path"])
        text = (folder / "transcript.txt").read_text(encoding="utf-8")
        info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
        if hashlib.sha256((folder / "ideal" / "audio.wav").read_bytes()).hexdigest() != info["audio_sha256"]:
            raise ValueError(f"Audio checksum mismatch: {entry['id']}")
        for variant in ("ideal", "flawed_level_1", "flawed_level_2", "flawed_level_3"):
            dest = folder / variant
            audio = load_audio(str(dest / "audio.wav"))
            duration = len(audio) / SAMPLE_RATE
            alignment = Alignment.model_validate_json((dest / "alignment.json").read_text(encoding="utf-8"))
            validate_alignment(alignment, text, duration)
            if variant != "ideal":
                labels = json.loads((dest / "flaw_labels.json").read_text(encoding="utf-8"))
                if submission and entry["kind"] == "real_speech" and not labels.get("human_reviewed"):
                    raise ValueError(f"Review flaw labels: {entry['id']} {variant}")
                for label in labels["flaw_regions"]:
                    if not 0 <= label["start_time"] < label["end_time"] <= duration + 0.025:
                        raise ValueError(f"Invalid label bounds: {entry['id']} {variant}")
            checked += 1
    print(f"Validated {len(speeches)} baseline groups, {checked} audio/alignment pairs; {len(real)} reviewed real speeches")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", action="store_true")
    validate(parser.parse_args().submission)
