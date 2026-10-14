"""Build controlled synthetic fixtures or import attributed real recordings."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import librosa
import numpy as np
import soundfile as sf
from backend.config import DATASET_DIR, SAMPLE_RATE
from backend.core.alignment import align_transcript, validate_alignment
from backend.core.audio import load_audio
from backend.models.schemas import Alignment, Word

TEXTS = [
    "Small steps create lasting change when people work together with courage and purpose.",
    "Education opens doors and gives every community the power to imagine a better future.",
    "Our shared responsibility is to protect nature and build a healthier world for everyone.",
    "Innovation begins with a question and grows when we listen carefully to one another.",
    "Leadership means serving others speaking honestly and choosing hope even in difficult times.",
]


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def synthetic_signal(text: str, voice: int):
    """Harmonic tones, NOT human speech; generated anchors have exact sample offsets."""
    pieces, words, cursor = [], [], 0
    for i, token in enumerate(text.split()):
        length = 0.32 + len(token) * 0.018
        t = np.arange(round(length * SAMPLE_RATE)) / SAMPLE_RATE
        f0 = (120 + voice * 20) * 2 ** ((2 * np.sin(2 * np.pi * 2.3 * t) + 1.4 * np.sin(i)) / 12)
        phase = 2 * np.pi * np.cumsum(f0) / SAMPLE_RATE
        envelope = np.sin(np.pi * np.linspace(0, 1, len(t))) ** 0.4
        signal = (np.sin(phase) + 0.3 * np.sin(2 * phase) + 0.1 * np.sin(3 * phase)) * envelope * (0.15 + 0.04 * np.sin(i))
        words.append(Word(word=token, start=cursor / SAMPLE_RATE, end=(cursor + len(signal)) / SAMPLE_RATE))
        gap = np.zeros(round((0.32 if i % 5 == 4 else 0.10) * SAMPLE_RATE))
        pieces.extend([signal, gap])
        cursor += len(signal) + len(gap)
    return np.concatenate(pieces).astype(np.float32), Alignment(method="synthetic", words=words)


def create_variants(folder: Path, audio: np.ndarray, alignment: Alignment, speech_id: str):
    (folder / "ideal").mkdir(parents=True, exist_ok=True)
    sf.write(folder / "ideal" / "audio.wav", audio, SAMPLE_RATE, subtype="PCM_16")
    write_json(folder / "ideal" / "alignment.json", alignment.model_dump())
    for level, rate, gain in [(1, 1.65, 0.10), (2, 1.35, 0.35), (3, 1.12, 0.75)]:
        variant = librosa.effects.time_stretch(audio, rate=rate)
        n = len(variant)
        start, end = n // 3, 2 * n // 3
        variant[start:end] *= gain
        dest = folder / f"flawed_level_{level}"
        dest.mkdir(parents=True, exist_ok=True)
        sf.write(dest / "audio.wav", variant, SAMPLE_RATE, subtype="PCM_16")
        words = [Word(word=w.word, start=w.start / rate, end=min(w.end / rate, n / SAMPLE_RATE), confidence=w.confidence) for w in alignment.words]
        write_json(dest / "alignment.json", Alignment(method=alignment.method, words=words).model_dump())
        severity = {1: 1.0, 2: 0.6, 3: 0.25}[level]
        labels = [
            {"type": "pacing_too_fast", "category": "pacing", "start_time": 0, "end_time": n / SAMPLE_RATE,
             "severity": severity, "description": f"Global pitch-preserving speed multiplier {rate}"},
            {"type": "volume_too_quiet", "category": "volume", "start_time": start / SAMPLE_RATE,
             "end_time": end / SAMPLE_RATE, "severity": severity,
             "description": f"Local amplitude multiplier {gain}; {20 * np.log10(gain):.2f} dB"},
        ]
        write_json(dest / "flaw_labels.json", {"speech_id": speech_id, "flaw_level": level,
                   "label_method": "known_transform", "human_reviewed": False, "flaw_regions": labels})


def build_demo(root: Path = DATASET_DIR):
    existing = json.loads((root / "metadata.json").read_text(encoding="utf-8"))["speeches"] if (root / "metadata.json").exists() else []
    demo_ids = {f"demo_{i:03d}" for i in range(1, len(TEXTS) + 1)}
    if any(e["id"] in demo_ids and e.get("kind") != "synthetic_fixture" for e in existing):
        raise ValueError("Demo IDs collide with imported recordings; generation will not overwrite them")
    entries = []
    for i, text in enumerate(TEXTS, 1):
        speech_id = f"demo_{i:03d}"
        folder = root / "speeches" / speech_id
        audio, alignment = synthetic_signal(text, i)
        create_variants(folder, audio, alignment, speech_id)
        (folder / "transcript.txt").write_text(text + "\n", encoding="utf-8")
        info = {"id": speech_id, "title": f"Controlled fixture {i}", "speaker": "Harmonic signal generator",
                "source": "Generated locally from original text", "license": "CC0-1.0", "kind": "synthetic_fixture",
                "human_reviewed": False, "duration_seconds": len(audio) / SAMPLE_RATE,
                "audio_sha256": hashlib.sha256((folder / "ideal" / "audio.wav").read_bytes()).hexdigest()}
        write_json(folder / "info.json", info)
        entries.append({**info, "path": f"speeches/{speech_id}", "variants": [1, 2, 3]})
    existing = json.loads((root / "metadata.json").read_text(encoding="utf-8"))["speeches"] if (root / "metadata.json").exists() else []
    write_json(root / "metadata.json", {"schema_version": 1, "speeches": [e for e in existing if e["id"] not in {x["id"] for x in entries}] + entries})
    print(f"Generated {len(entries)} controlled fixtures and 15 flawed variants. These are not real speeches.")


def import_manifest(manifest: Path, root: Path = DATASET_DIR):
    source_entries = json.loads(manifest.read_text(encoding="utf-8"))["speeches"]
    if not source_entries:
        raise ValueError("Manifest has no speeches; add >=5 reviewed sources for submission")
    entries = json.loads((root / "metadata.json").read_text(encoding="utf-8"))["speeches"] if (root / "metadata.json").exists() else []
    for item in source_entries:
        sid = item["id"]
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", sid):
            raise ValueError("Source ID must be a simple slug")
        if not item.get("license") or not item.get("source"):
            raise ValueError("Each source needs a permission/license note and attribution URL")
        if any(e["id"] == sid for e in entries):
            raise ValueError(f"ID {sid} already exists; use a new ID to preserve reviewed data")
        audio = load_audio(str((manifest.parent / item["audio_path"]).resolve()))
        if item.get("transcript_path"):
            text = (manifest.parent / item["transcript_path"]).read_text(encoding="utf-8-sig").strip()
        else:
            import whisperx
            model = whisperx.load_model("small.en", "cpu", compute_type="int8")
            transcription = model.transcribe(audio, batch_size=1, language="en")
            text = " ".join(s["text"].strip() for s in transcription["segments"])
        alignment = Alignment.model_validate_json((manifest.parent / item["alignment_path"]).read_text(encoding="utf-8")) if item.get("alignment_path") else align_transcript(audio, text)
        validate_alignment(alignment, text, len(audio) / SAMPLE_RATE)
        folder = root / "speeches" / sid
        create_variants(folder, audio, alignment, sid)
        (folder / "transcript.txt").write_text(text + "\n", encoding="utf-8")
        info = {"id": sid, "title": item["title"], "speaker": item["speaker"], "source": item["source"],
                "license": item["license"], "kind": "real_speech", "human_reviewed": bool(item.get("human_reviewed", False)),
                "duration_seconds": len(audio) / SAMPLE_RATE,
                "audio_sha256": hashlib.sha256((folder / "ideal" / "audio.wav").read_bytes()).hexdigest()}
        write_json(folder / "info.json", info)
        entries.append({**info, "path": f"speeches/{sid}", "variants": [1, 2, 3]})
        write_json(root / "metadata.json", {"schema_version": 1, "speeches": entries})
        print(f"Imported {sid}; review text, transformed timings, labels, and baseline delivery quality")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true")
    group.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    build_demo() if args.demo else import_manifest(args.manifest)
