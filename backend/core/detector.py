"""Compare matched word neighborhoods and merge only same-type adjacent deviations."""
import numpy as np
from backend.core.classifier import RULES, classify
from backend.core.explainer import explain
from backend.models.schemas import Alignment, Delta, Flaw


def detect_flaws(baseline: dict, participant: dict, alignment: Alignment, threshold: float = 1.5) -> list[Flaw]:
    flaws = []
    for feature, b in baseline.items():
        p = participant[feature]
        _, _, _, unit, floor = RULES[feature]
        valid = np.isfinite(b) & np.isfinite(p)
        scale = max(float(np.std(b[np.isfinite(b)])) if np.isfinite(b).any() else 0, floor)
        z = (p - b) / scale
        labels = [classify(feature, float(z[i]))[1] if valid[i] and abs(z[i]) > threshold else None for i in range(len(b))]
        i = 0
        while i < len(labels):
            if labels[i] is None:
                i += 1
                continue
            j = i + 1
            while j < len(labels) and labels[j] == labels[i] and alignment.words[j].start - alignment.words[j - 1].end <= 0.25:
                j += 1
            a, end = alignment.words[i].start, alignment.words[j - 1].end
            if feature == "pause_gap":
                # Ground a pause in the actual gap after the word. Missing pauses use the boundary.
                a = alignment.words[i].end
                end = alignment.words[j].start if j < len(alignment.words) else end
                if end <= a:
                    a = max(alignment.words[i].start, a - 0.08)
                    end = alignment.words[i].end
            magnitude = float(np.mean(np.abs(z[i:j])))
            severity = min(1.0, max(0.1, (magnitude - threshold) / 3 + 0.25))
            delta = Delta(baseline=round(float(np.mean(b[i:j])), 5), participant=round(float(np.mean(p[i:j])), 5),
                          z_score=round(float(np.mean(z[i:j])), 5), scale=round(scale, 5), unit=unit)
            category, kind = classify(feature, delta.z_score)
            text = " ".join(w.word for w in alignment.words[i:j])
            flaws.append(Flaw(id="", type=kind, category=category, start_time=round(a, 4), end_time=round(end, 4),
                severity=round(severity, 4), severity_label="severe" if severity >= 0.75 else "moderate" if severity >= 0.45 else "minor",
                transcript_segment=text, feature_deltas={feature: delta}, causal_explanation=explain(kind, feature, delta, text)))
            i = j
    flaws.sort(key=lambda f: (f.start_time, f.category, f.type))
    for i, flaw in enumerate(flaws):
        flaw.id = f"flaw_{i + 1:03d}"
    return flaws
