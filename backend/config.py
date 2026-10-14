"""One place for processing limits and paths."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = Path(os.getenv("SPEECH_DATASET_DIR", ROOT / "dataset"))
SAMPLE_RATE = 16_000
HOP_LENGTH = 320  # 20 ms between frames
FRAME_LENGTH = 1024
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_DURATION_SECONDS = 600
ALGORITHM_VERSION = "1.0.0"
RESULT_LIMIT = 64
