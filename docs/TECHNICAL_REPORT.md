# Cadence: technical report

Track C - Contrastive Speech Analytics and Temporal Flaw Grounding. Implementation version 1.0.0, 12 October 2026. This report can be exported as five pages using `scripts/build_technical_report.py`.

## 1. Architecture and implementation state

FastAPI accepts in-memory audio uploads and baseline selections. Python modules separate validation, alignment, signal extraction, comparison, scoring, explanations, and orchestration. A shared browser controller powers a local dashboard and an optional Next.js shell. Processing is CPU-based; one concurrent analysis is allowed to bound memory. Baseline feature results use a bounded cache, and the last 64 JSON analyses are retained in memory.

The local pipeline and upload API passed 17 behavioral tests. Five synthetic fixture groups were generated with ideal plus three modified versions, totaling 20 WAV files. The fixtures are harmonic signals associated with generated word anchors; they are **not spoken performances**. No reviewed real-speech corpus has yet been imported. The optional WhisperX inference, Next.js build, Docker image runtime, and full browser interactions are not verified. Docker Compose configuration parses successfully.

## 2. Contrastive data construction and provenance

Each baseline group contains attribution/review metadata, a transcript, an ideal WAV and alignment JSON, and three flawed-variant folders containing WAV, mapped alignment, and injected-flaw labels. Metadata includes source, license note, speaker, content checksum, media kind, duration, and human-review flag.

The implemented manipulation gradient preserves text and pitch while increasing global speaking rate: 1.65x (severe), 1.35x (moderate), and 1.12x (subtle). A middle-third segment is attenuated with amplitude factors 0.10, 0.35 and 0.75. Known sample offsets generate injection labels; word anchors are divided by the speed factor. Phase-vocoder transients can perturb phonetic boundaries, so these mapped anchors need listening review on real speech. Injection labels are never read by the inference pipeline; they are used only by evaluation.

The real-data importer accepts locally downloaded recordings with verified transcripts and optional reviewed timings, or uses optional WhisperX for missing text/timings. The submission integrity gate requires at least five reviewed real baseline recordings and reviewed flawed labels. A public dataset URL remains pending. Filler insertion, vocal fry, intentional monotone synthesis, and isolated misplaced-pause generation are not yet part of the dataset builder.

## 3. Features and alignment

Input decoding supports WAV, MP3 and FLAC through SoundFile. Recordings must be 0.5-600 seconds, <=50 MB, finite and audible. Channels are averaged to mono, then resampled to 16 kHz with rational polyphase resampling. Peak normalization is avoided because it can obscure volume evidence.

A 1024-sample frame (64 ms) and 320-sample hop (20 ms) produce a common frame grid. Features include 13 MFCCs from log mel power spectra; YIN pitch between 60 and 500 Hz; periodicity- and energy-gated voiced F0; RMS amplitude; relative dB; spectral centroid, rolloff, flatness, zero-crossing rate; and energy-derived pause intervals. Null values represent unreliable/unvoiced pitch. Rate uses an English vowel-group syllable-count heuristic over aligned words and local neighborhoods.

Speaker pitch is centered in semitones: p(t)=12 log2(F0(t)/median(voiced F0)). This removes absolute voice depth while preserving relative pitch variation. Volume uses e(t)=20 log10(RMS(t)/speaker reference RMS), where the reference is the voiced 75th percentile. This removes global gain differences while preserving local emphasis. Independently standardizing each contour to unit variance would suppress monotone and uniform-volume evidence, so that planning suggestion was changed.

Reviewed supplied timing JSON is supported. Optional WhisperX aligns the transcript on CPU, and its English model is loaded lazily. Approximate timing distributes words by token length over recording duration; the UI explicitly labels its boundaries and pacing as provisional. Corresponding word starts/ends map baseline features onto participant time with piecewise linear interpolation. Mismatched transcripts/tokenization, unordered timing, and out-of-range intervals are rejected.

## 4. Detection, explanations and scoring

Word neighborhoods summarize local pitch range (90th minus 10th percentile in relative semitones), syllable rate, relative energy, following pause gap, and spectral flatness. For feature f and matched word i, deviation d_i=(p_i-b_i)/s_f, where s_f=max(std(b), feature floor). Floors are 0.8 semitones, 0.8 syllables/s, 3 dB, 0.15 seconds and 0.06 flatness units. The default threshold is |d|>1.5. These are interpretable heuristic deviations; a single reference does not support calibrated statistical significance or probabilities.

The signed delta chooses a rule label: faster/slower, reduced/excessive pitch range, quieter/louder local energy, missing/extra pause, or spectral change. Same-type adjacent flagged words are merged when separated by <=0.25 seconds. Missing pauses are grounded near the expected word boundary, since an absent pause has no actual audio interval. Spectral change is a clarity proxy and is explicitly not a diagnosis of articulation quality or rhetorical intent.

Explanations contain observed participant/baseline values, units, the exact deviation formula, and a deterministic practice suggestion. They document acoustic evidence associated with a delivery difference, not experimentally established rhetorical causality.

Five rubric dimensions are scored from 1 to 10. For dimension k, score_k=clip(10-9*integral(max active severity_k)/duration,1,10). Taking maximum active severity prevents double-counting overlapping regions. Overall score is the equal-weight rubric mean times ten. Scores measure reference similarity, not validated competition quality.

## 5. Evaluation, reproducibility and limits

SHA256-based analysis IDs include input audio, baseline audio, both alignments, transcript, baseline ID, threshold and algorithm version. The core has no stochastic inference, wall-clock metadata, external scoring API, or random IDs. Three repeated fixture analyses produce identical JSON. Optional model inference still needs separate environment/model-version verification before claiming cross-machine reproducibility.

Behavioral tests cover identical input producing 100 with no flaws, severity ordering, three-run repeatability, frame dimensions and finite/null handling, gain normalization, silence/noise/short audio, time mapping, path traversal, HTTP upload/cache, and approximate timing disclosure. Dataset validation checks checksums, bounds, transcript consistency and all variant assets.

The label-aware fixture report records prediction precision, label recall, interval overlap and mean boundary error. Current controlled-fixture metrics are approximately 0.786 precision, 0.800 recall and 0.520 seconds mean boundary error. Matching requires the same type and positive temporal overlap; fragmented predictions are pooled for label coverage. The permissive overlap criterion and pooled intervals can inflate apparent coverage, so these results must not be presented as competition accuracy. They neither meet every target nor establish performance on human speech.

Next validation must use held-out real speeches split by source/speaker, independently reviewed word boundaries and labels, minimum-IoU matching, per-category precision/recall, boundary-error distributions, microphone/speaker sensitivity and severity ordering. The UI's displayed times are in participant seconds; frame spacing alone is not a precision guarantee. Noisy/unvoiced inputs receive reliability warnings.

References: librosa 0.11.0 feature documentation; m-bain/WhisperX repository and WhisperX: Time-Accurate Speech Transcription of Long-Form Audio (2023); Next.js App Router installation documentation.
