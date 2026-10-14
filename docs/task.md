# Task Tracker
# Contrastive Speech Analytics & Temporal Flaw Grounding

**Last Updated**: October 12, 2026  
**Status**: Runnable local prototype; real dataset and external deliverables still open

---

## Legend
- ✅ Done
- 🔄 In Progress
- 🔲 TODO
- ❌ Blocked
- ⏭️ Skipped

---

## Phase 0: Planning & Documentation
| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Read and analyze problem statement | ✅ | Extracted from PDF |
| 0.2 | Create PRD (Product Requirements Document) | ✅ | `docs/PRD.md` |
| 0.3 | Create TDD (Technical Design Document) | ✅ | `docs/TDD.md` |
| 0.4 | Create Implementation Strategy | ✅ | `docs/implementation_strategy.md` |
| 0.5 | Create Task Tracker | ✅ | This file |
| 0.6 | Create EverythingYouShouldKnow guide | ✅ | `docs/everythingyoushouldknow.md` |
| 0.7 | Get user approval on plan | ? | Implementation authorized by the user on 2026-10-12 |

---

## Phase 1: Contrastive Dataset Construction
| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Set up dataset directory structure | ? | Directory layout and generated artifacts exist |
| 1.2 | Source 5+ ideal speech recordings | ?? | Five source pages researched in docs/DATASET_SOURCES.md; no reviewed recordings imported |
| 1.3 | Download and convert audio to WAV 16kHz mono | ? | Downloader written; actual download blocked by configured network proxy |
| 1.4 | Transcribe all ideal speeches with Whisper | ?? | Optional WhisperX importer implemented; real transcription/model inference pending |
| 1.5 | Generate flawed Level 1 (egregiously bad) | ?? | Severe controlled fixtures generated; real variants pending |
| 1.6 | Generate flawed Level 2 (moderately bad) | ?? | Moderate controlled fixtures generated; real variants pending |
| 1.7 | Generate flawed Level 3 (almost perfect) | ?? | Subtle controlled fixtures generated; real variants pending |
| 1.8 | Run forced alignment on all audio variants | ?? | Exact generated anchors and transformed timings exist; real WhisperX/review pending |
| 1.9 | Create flaw labels for all flawed variants | ?? | Known-transform fixture labels generated; human review pending |
| 1.10 | Create dataset metadata.json | ? | Master metadata and provenance/checksums created |
| 1.11 | Validate dataset integrity | ?? | 20 fixture audio/alignment pairs pass integrity; submission gate correctly rejects fixture-only dataset |

---

## Phase 2: Audio Processing Pipeline (Backend Core)
| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Set up Python project structure | ? | Importable backend packages and FastAPI app |
| 2.2 | Install dependencies (librosa, whisperx, etc.) | ?? | Core packages installed; optional WhisperX/model environment unverified |
| 2.3 | Build `features.py` — MFCC extraction | ? | 13 log-mel MFCCs extracted and shape-tested |
| 2.4 | Build `features.py` — F0/pitch extraction | ? | YIN with periodicity/energy gate; null unvoiced pitch. Changed from planned pYIN for CPU speed |
| 2.5 | Build `features.py` — Energy/RMS extraction | ? | RMS and relative dB contours |
| 2.6 | Build `features.py` — Speech rate computation | ? | Heuristic English syllables/s with word timing |
| 2.7 | Build `features.py` — Pause detection | ? | Energy-derived pause intervals and aligned boundary gaps |
| 2.8 | Build `features.py` — Spectral features (FFT) | ? | STFT, centroid, rolloff, flatness and ZCR |
| 2.9 | Build `features.py` — Speaker normalization | ? | Median-centered semitones and relative dB preserve variation; gain invariance tested |
| 2.10 | Build `alignment.py` — Forced alignment wrapper | ?? | WhisperX wrapper and validated supplied JSON; actual model inference pending |
| 2.11 | Build `alignment.py` — Time axis alignment | ? | Corresponding-word piecewise time mapping tested |
| 2.12 | Write unit tests for feature extraction | ? | Signal shapes, voiced/null behavior, invalid inputs, resampling and invariance tested |

---

## Phase 3: Flaw Detection & Scoring Engine
| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Build `detector.py` — Z-score deviation detection | ? | Matched-word deltas with feature-specific spread floors; heuristic rather than statistical significance |
| 3.2 | Build `detector.py` — Contiguous region finder | ? | Same-type contiguous regions; participant-time grounding |
| 3.3 | Build `classifier.py` — Flaw type classification | ? | Signed feature rules for tone, pace, volume, pauses and spectral clarity proxy |
| 3.4 | Build `scorer.py` — Rubric scoring (5 dimensions) | ? | Five bounded duration-weighted rubric scores; overlaps not double-counted |
| 3.5 | Build `explainer.py` — Causal explanation generator | ? | Deterministic measured summary, formula and practice suggestion |
| 3.6 | Build API endpoint `POST /api/analyze` | ? | Multipart upload, alias compare endpoint and result retrieval tested |
| 3.7 | Build API endpoint `GET /api/baselines` | ? | Baseline index, media and health endpoints tested |
| 3.8 | Write integration tests for analysis pipeline | ? | 17 behavioral tests including multipart upload and errors pass |
| 3.9 | Verify reproducibility (3 identical runs) | ? | Three fixture runs produce identical JSON and content IDs |

---

## Phase 4: Interactive Dashboard (Frontend)
| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Initialize Next.js project | ?? | Next.js App Router shell written; npm network/cache prevents dependency install/build |
| 4.2 | Set up design system (CSS variables, fonts) | ? | Shared CSS variables, local typography and responsive layouts written |
| 4.3 | Build Header component | ? | Shared dashboard header and connectivity state |
| 4.4 | Build Upload Panel (audio dropzone) | ? | Dropzone and audio file input wired |
| 4.5 | Build Transcript Input | ? | Baseline text, editable transcript and .txt upload wired |
| 4.6 | Build Baseline Selector | ? | Baseline dropdown loads real API metadata |
| 4.7 | Build Overall Score display (animated) | ?? | Overall score display implemented; planned count-up animation pending |
| 4.8 | Build Rubric Radar Chart | ? | SVG radar instead of Chart.js; shared dependency-free runtime |
| 4.9 | Build Waveform Viewer with flaw regions | ? | Canvas waveform from actual decoded audio, flaw overlays and playback controls written |
| 4.10 | Build Feature Comparison Charts (F0, energy, rate) | ? | Mapped SVG pitch, energy, rate, raw F0 and centroid overlays written |
| 4.11 | Build Flaw Cards panel | ? | Explanation cards, inspectable math and segment playback written |
| 4.12 | Build Highlighted Transcript view | ? | Clickable aligned words and synchronized highlighting written |
| 4.13 | Add micro-animations and transitions | ? | Hover/focus transitions, busy animation and reduced-motion handling |
| 4.14 | Responsive layout testing | ? | Breakpoints written; browser QA blocked by disconnected connector and Windows subprocess permissions |

---

## Phase 5: Integration, Polish & Deliverables
| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Wire frontend to backend API | ? | Shared controller connects to actual API; static routes and multipart flow tested |
| 5.2 | End-to-end testing with real dataset | ?? | Fixture pipeline/API verified; real-speech and full browser E2E pending |
| 5.3 | Edge case testing (silence, noise, short audio) | ? | Silence, noise, short/nonfinite inputs, gain, transcript mismatch and traversal tested |
| 5.4 | Create Dockerfile for backend | ? | Backend image definition written; image build/runtime unverified |
| 5.5 | Create Dockerfile for frontend | ? | Optional Next.js image definition written; image build/runtime unverified |
| 5.6 | Create docker-compose.yml | ? | Default backend + optional next profile; docker compose config passes |
| 5.7 | Write README.md | ? | Setup, usage, limitations, import, tests and revision commands documented |
| 5.8 | Write Technical Documentation (≤6 pages) | ? | Technical markdown and validated five-page PDF created |
| 5.9 | Host dataset on GitHub/Google Drive | ?? | Public dataset/repository hosting not performed |
| 5.10 | Record demo video (3-10 min) | ?? | Seven-minute demo narrative prepared; recording/upload pending |
| 5.11 | Final code cleanup and comments | ? | Separated modules, deterministic explanations, review guide and collaboration conventions |
| 5.12 | Submit to DevPost | ?? | Submission pending real data, verification and external deliverables |

---

## Change Log

| Date | Change | Details |
|---|---|---|
| 2026-10-12 | Initial creation | Created all planning documents |
| 2026-10-12 | First implementation | Local prototype, five fixture groups, 17 passing tests, source shortlist, five-page PDF and complete revision guide |

## Verification record

- `python -m pytest -q`: 17 passed; one third-party Starlette/httpx deprecation warning.
- Dataset integrity: five groups and 20 audio/alignment pairs pass.
- Repeatability: three identical inputs produce byte-identical report JSON.
- JavaScript syntax: `node --check frontend/public/dashboard.js` passes.
- HTTP: local dashboard and health endpoints return 200.
- Compose: `docker compose config --quiet` passes; images were not built.
- Technical PDF: five pages, verified with pypdf.
- Controlled evaluation: precision 0.786, recall 0.800, mean boundary error 0.520s; permissive overlap matching, not real-speech validation.
- Browser QA: connector disconnected; isolated runner could not start due Windows subprocess permission error. Script exists for later execution.
- Next.js: source written; dependencies/build unavailable through the current npm proxy/cache.
- Real-source download: normal request blocked by configured network proxy.
