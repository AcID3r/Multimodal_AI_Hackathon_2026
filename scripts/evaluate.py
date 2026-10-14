"""Label-aware stress report: precision, recall, interval IoU and boundary error.

Fixtures verify software behavior, not speech-evaluation accuracy.
"""
import json
from pathlib import Path
from backend.config import ROOT
from backend.core.dataset import get_baseline, list_baselines
from backend.core.pipeline import analyze
from backend.models.schemas import Alignment


def iou(a, b):
    intersection = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = max(a[1], b[1]) - min(a[0], b[0])
    return intersection / union if union else 0


def evaluate():
    runs, boundary_errors = [], []
    label_hits = label_misses = prediction_hits = prediction_misses = 0
    for entry in list_baselines():
        _, folder, text, b_align = get_baseline(entry["id"])
        for level in (1, 2, 3):
            variant = folder / f"flawed_level_{level}"
            alignment = Alignment.model_validate_json((variant / "alignment.json").read_text(encoding="utf-8"))
            result = analyze((variant / "audio.wav").read_bytes(), entry["id"], folder / "ideal" / "audio.wav", text, b_align, alignment)
            labels = json.loads((variant / "flaw_labels.json").read_text(encoding="utf-8"))["flaw_regions"]
            # A global pacing transform can produce several phrase regions. Merge same-type
            # predictions for coverage, but retain original counts for false-positive reporting.
            matched_predictions, overlaps = set(), []
            missed = 0
            for label in labels:
                matches = [(i, f) for i, f in enumerate(result.flaw_regions) if f.type == label["type"] and iou((f.start_time, f.end_time), (label["start_time"], label["end_time"])) > 0]
                if not matches:
                    missed += 1
                    continue
                matched_predictions.update(i for i, _ in matches)
                predicted = (min(f.start_time for _, f in matches), max(f.end_time for _, f in matches))
                overlap = iou(predicted, (label["start_time"], label["end_time"]))
                overlaps.append(overlap)
                boundary_errors.extend([abs(predicted[0] - label["start_time"]), abs(predicted[1] - label["end_time"])])
            hits = len(labels) - missed
            false = len(result.flaw_regions) - len(matched_predictions)
            label_hits += hits; label_misses += missed
            prediction_hits += len(matched_predictions); prediction_misses += false
            runs.append({"baseline_id": entry["id"], "kind": entry["kind"], "level": level,
                         "overall_score": result.overall_score, "label_hits": hits, "label_misses": missed,
                         "unmatched_predictions": false, "mean_interval_iou": sum(overlaps) / len(overlaps) if overlaps else 0})
    report = {"scope": "Controlled fixtures are not evidence of human speech accuracy",
              "matching": "same type and positive overlap; fragmented predictions pooled per label",
              "precision": prediction_hits / (prediction_hits + prediction_misses) if prediction_hits + prediction_misses else 0,
              "recall": label_hits / (label_hits + label_misses) if label_hits + label_misses else 0,
              "mean_boundary_error_seconds": sum(boundary_errors) / len(boundary_errors) if boundary_errors else None,
              "runs": runs}
    dest = ROOT / "reports" / "evaluation.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "runs"}, indent=2))
    print(f"Saved {dest}")
    return report


if __name__ == "__main__":
    evaluate()
