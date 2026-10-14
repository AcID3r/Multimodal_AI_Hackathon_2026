"""Transcript alignment and mapping by corresponding words (never by recording time)."""
import re
from functools import lru_cache
import numpy as np
from backend.config import SAMPLE_RATE
from backend.models.schemas import Alignment, Word


def tokens(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.casefold())


def validate_alignment(alignment: Alignment, transcript: str, duration: float) -> Alignment:
    if tokens(" ".join(w.word for w in alignment.words)) != tokens(transcript):
        raise ValueError("Alignment words must match the baseline transcript exactly")
    previous_end = 0.0
    for word in alignment.words:
        if word.start < previous_end - 0.03 or word.end > duration + 0.025:
            raise ValueError("Alignment intervals overlap, are out of order, or exceed audio duration")
        previous_end = word.end
    return alignment


def estimate_alignment(audio: np.ndarray, transcript: str) -> Alignment:
    """Explicitly approximate fallback. It is NOT forced alignment."""
    words = transcript.split()
    if not words:
        raise ValueError("Transcript is empty")
    weights = np.array([max(1, len(tokens(word)[0])) if tokens(word) else 1 for word in words])
    boundaries = np.r_[0, np.cumsum(weights) / weights.sum() * (len(audio) / SAMPLE_RATE)]
    return Alignment(method="estimated", words=[Word(word=w, start=float(boundaries[i]),
                     end=float(boundaries[i + 1])) for i, w in enumerate(words)])


@lru_cache(maxsize=1)
def _alignment_model():
    try:
        import whisperx
    except ImportError as exc:
        raise ValueError("WhisperX is not installed. Supply word-timing JSON or select approximate mode; see README.") from exc
    return whisperx.load_align_model(language_code="en", device="cpu")


def align_transcript(audio: np.ndarray, transcript: str) -> Alignment:
    import torch
    import whisperx
    torch.manual_seed(0)
    torch.set_num_threads(1)
    model, metadata = _alignment_model()
    result = whisperx.align([{"text": transcript, "start": 0.0, "end": len(audio) / SAMPLE_RATE}],
                           model, metadata, audio, "cpu", return_char_alignments=False)
    words = []
    for item in result["word_segments"]:
        if "start" not in item or "end" not in item or item["end"] <= item["start"]:
            raise ValueError("WhisperX could not align every word; correct the transcript or supply reviewed timings")
        words.append(Word(word=item["word"], start=item["start"], end=item["end"], confidence=item.get("score")))
    return validate_alignment(Alignment(method="whisperx", words=words), transcript, len(audio) / SAMPLE_RATE)


def map_times(times: np.ndarray, baseline: Alignment, participant: Alignment) -> np.ndarray:
    """Piecewise linear mapping using starts/ends of the same words as anchors."""
    source, target = [0.0], [0.0]
    for b, p in zip(baseline.words, participant.words, strict=True):
        for s, t in [(p.start, b.start), (p.end, b.end)]:
            if s > source[-1]:
                source.append(s)
                target.append(t)
    return np.interp(times, source, target)
