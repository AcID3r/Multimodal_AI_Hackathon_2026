# Cadence - Contrastive Speech Analytics

A CPU-based prototype for Track C: compare deliveries of the **same transcript**, extract acoustic features, locate differences, and produce repeatable rubric scores with measured explanations.

**Current state:** the local dashboard, processing pipeline, HTTP API, dataset builder, and behavioral tests run. Five controlled synthetic fixture groups (20 WAV files) are generated locally. **These are harmonic tones, not real speeches, and do not satisfy the competition's real baseline dataset requirement.** Real speech import is implemented; real source collection and human review remain unfinished. Check [the task tracker](docs/task.md).

## Start on Windows

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m scripts.build_dataset --demo
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. API docs: **http://127.0.0.1:8000/docs**.

For later starts, run `powershell -ExecutionPolicy Bypass -File scripts/start.ps1`.
On Linux/macOS, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.
Python 3.11 is the reference runtime. The implementation session used a virtual environment that can read existing system packages; use a clean environment for reproducible setup.

## Use it

1. Choose a baseline. Use the Reference / Subtle / Moderate / Severe buttons for controlled fixture comparisons.
2. For your own recording, read the **same transcript** as a real baseline and upload WAV, MP3, or FLAC.
3. Supply word-timing JSON, use optional WhisperX, or explicitly select approximate timing. Approximate results are provisional, not precise forced alignment.
4. Inspect the waveform and mapped feature overlays. Play a flaw section or click a transcript word to seek.
5. Inspect the mathematical evidence and export the result JSON.

Audio remains in memory and is discarded after analysis. The last 64 result objects are cached in memory and disappear on restart. There is no authentication; default startup binds to loopback.

## Timing JSON

```json
{"method":"provided","words":[{"word":"Hello","start":0.1,"end":0.6},{"word":"world","start":0.7,"end":1.1}]}
```

Words must match the baseline transcript, in order, and intervals must lie within the recording. Word confidence is optional. There is no silent substitution of approximate timing for failed forced alignment.

## Import real speeches

Copy `dataset/sources.example.json` to `dataset/sources.json`, replace every example field with actual attribution, permission/license information, and local file paths, and add at least five recordings. Incoming paths are relative to the manifest directory.

```powershell
.\.venv\Scripts\python.exe -m scripts.build_dataset --manifest dataset/sources.json
.\.venv\Scripts\python.exe -m scripts.validate_dataset
```

Each recording gets an ideal and three flawed variants. Transformations preserve the transcript: pitch-preserving speed multipliers 1.65 / 1.35 / 1.12 and local amplitude multipliers 0.10 / 0.35 / 0.75. Labels record exact transform boundaries; word anchors are mapped through the known speed transform. **Review transformed word timings by listening before using them as evaluation ground truth.**

For URL excerpts, install yt-dlp, ensure ffmpeg is on PATH, add explicit URLs and excerpt bounds to the manifest, and run `python -m scripts.download_sources --manifest dataset/sources.json`. Candidate source pages are in [DATASET_SOURCES.md](docs/DATASET_SOURCES.md); no recording has yet been downloaded.

If transcript/alignment paths are omitted, the importer calls optional WhisperX transcription/alignment. Review transcripts, baseline quality, boundaries, and labels; set `human_reviewed` in both metadata and label files only after that review.

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_dataset --submission
```

This check deliberately fails until at least five reviewed real recordings and their reviewed variant labels exist. Dataset media is ignored by Git by default; publish permission-reviewed media to a repository or public Drive and replace this README's pending dataset link before submission.

**Public dataset link: pending.**

## Optional WhisperX

WhisperX has substantial Torch and model dependencies. Its dependency constraints can conflict with the pinned core stack. Use a **separate environment**, install `backend/requirements-alignment.txt` together with FastAPI, uvicorn, python-multipart, librosa and soundfile, and let WhisperX resolve NumPy/Torch. Do not force the core NumPy pin into that environment. This optional environment and actual model inference have not been verified here.

Alignment runs on CPU and downloads an English alignment model on first use. Transcription defaults to `small.en` with int8 compute for practical CPU use, rather than the planning document's large-v3. Supplied reviewed JSON avoids model downloads entirely.

## Next.js frontend

The optional Next.js shell uses the **same** `frontend/public/dashboard.js` controller and stylesheet as the local dashboard:

```powershell
cd frontend
npm install
npm run typecheck
npm run build
npm run dev
```

Open http://localhost:3000 with the backend running. `NEXT_PUBLIC_API_URL` defaults to http://localhost:8000. The current environment restricts npm networking and has no cached Next.js package, so this shell is **written but not build-verified**. The shared browser code uses Canvas and SVG; Chart.js and WaveSurfer are not runtime dependencies.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.validate_dataset
.\.venv\Scripts\python.exe -m scripts.evaluate
node --check frontend/public/dashboard.js
```

Optional browser QA: install `backend/requirements-browser.txt`, keep the backend running, then run `python -m scripts.check_dashboard`. It uses an isolated headless Chrome/Edge with no existing browser profile. Its execution was blocked here by Windows subprocess permissions; the browser connector was also disconnected.

The tests cover identical audio, three repeated runs, severity ordering, speaker gain, null pitch on noise, silent/invalid input, frame shapes, time mapping, path traversal, HTTP upload, cache retrieval, and approximate-timing disclosure. Evaluation writes `reports/evaluation.json`; it evaluates controlled fixture labels and must not be presented as real-speech accuracy.

## Containers

```powershell
docker compose up --build
docker compose --profile next up --build
```

The default service serves the local dashboard on port 8000. The `next` profile adds the Next.js shell on port 3000. Images build their own fixtures; optional speech models are excluded. Container definitions are provided; image build/runtime verification is recorded in the task tracker.

## What to review

Read [the complete code review guide](docs/CODE_REVIEW_GUIDE.md), then [the technical report](docs/TECHNICAL_REPORT.md). The guide gives the exact file order, function-level questions, exercises, and commands for revising every source file.

The remaining submission work is real baseline collection/review, precision and boundary calibration on held-out speeches, full optional-model/Next.js/container verification, public dataset hosting, a 3-10 minute video, and DevPost submission. No repository or dataset has been published.

Implementation references: [librosa feature API](https://librosa.org/doc/0.11.0/feature.html), [WhisperX reference](https://github.com/m-bain/whisperX), [Next.js installation](https://nextjs.org/docs/app/getting-started/installation).
