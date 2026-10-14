# How to revise every part of Cadence

This guide describes **files that actually exist**, rather than the original planned component names. Read one section, run its example, then explain its functions without looking. Every later work session should update this guide and end with the changed-file reading order.

## 1. Understand the goal before the code

Read `problem_statement_extracted.txt`, `docs/PRD.md`, `docs/task.md`, `README.md`, and `docs/TECHNICAL_REPORT.md`. The TDD and implementation strategy retain the original plan; implementation notes explain where that plan changed.

Be able to answer: Why must paired recordings use the same words? Why are exact timestamps and measured explanations important? Which parts of the submission are still unfinished?

## 2. Understand the dataset

| Order | File | Functions or fields to revise | Check your understanding |
|---|---|---|---|
| 1 | `dataset/sources.example.json` | attribution, license, local paths, review flags | How do you add a real speech without inventing provenance? |
| 1b | `docs/DATASET_SOURCES.md`, `scripts/download_sources.py` | candidate URLs, safe slugs, excerpt bounds, downloader arguments | Why is a source shortlist different from an imported recording? |
| 2 | `scripts/build_dataset.py` | `synthetic_signal`, `create_variants`, `build_demo`, `import_manifest` | Trace a recording into its three flawed variants. Why do speed changes also change word timestamps? |
| 3 | `dataset/metadata.json` | `id`, `path`, `kind`, variants and review flags | Distinguish a signal fixture from real speech. |
| 4 | `dataset/speeches/demo_001/info.json` | source, license, SHA256 | What is a checksum used for? |
| 5 | `dataset/speeches/demo_001/transcript.txt` | original text | Why must every paired variant preserve it? |
| 6 | `dataset/speeches/demo_001/ideal/alignment.json` | word/start/end, method | Explain each timestamp and its provenance. |
| 7 | `dataset/speeches/demo_001/flawed_level_1/flaw_labels.json` | type, interval, severity, known transform | These are ground-truth labels; why must the detector not read them? |
| 8 | `scripts/validate_dataset.py` | `validate`, submission gate | What integrity errors can it catch? What cannot it assess by listening? |

Run `python -m scripts.validate_dataset` with your virtual-environment Python. Try `--submission` and explain why it correctly fails with only fixtures. Do not delete the dataset while revising; generation rewrites only the controlled demo IDs.

## 3. Read the backend from inputs to outputs

| Order | File | Functions or definitions | What to explain |
|---|---|---|---|
| 1 | `backend/config.py` | paths, sample rate, hop/frame size, upload/duration/cache limits | At 16 kHz, a 320-sample hop is 20 ms. A frame spans 64 ms, so feature precision is not equal to timestamp spacing. |
| 2 | `backend/models/schemas.py` | `Word`, `Alignment`, `Delta`, `Explanation`, `Flaw`, `Series`, `AnalysisResult` | Define the exact API contract; explain null pitch and allowed timing methods. |
| 3 | `backend/core/audio.py` | `load_audio` | Bytes -> decode -> limits -> mono -> finite/silence checks -> rational resampling. |
| 4 | `backend/core/alignment.py` | `tokens`, `validate_alignment`, `estimate_alignment`, `_alignment_model`, `align_transcript`, `map_times` | Supplied/forced/estimated timing, transcript validation, cached model, corresponding-word anchors. |
| 5 | `backend/core/features.py` | `Features`, `syllables`, `contiguous`, `detect_pauses`, `extract_features`, `word_measurements` | STFT, MFCC, YIN, periodicity gate, RMS, relative dB, semitones, rate, spectral proxies, word neighborhoods. |
| 6 | `backend/core/classifier.py` | `RULES`, `classify` | Signed deviation selects the label; floors give each feature a minimum meaningful scale. |
| 7 | `backend/core/explainer.py` | `ADVICE`, `explain` | Evidence is deterministic; a coaching suggestion is not proof of rhetorical causality. |
| 8 | `backend/core/detector.py` | `detect_flaws` | Matched participant-minus-baseline deltas, threshold, same-type merging, pause boundaries, severity and sorting. |
| 9 | `backend/core/scorer.py` | `DIMENSIONS`, `score` | Integrate maximum severity over time to avoid double-counting overlaps; keep scores in [1,10]. |
| 10 | `backend/core/dataset.py` | `safe_path`, `list_baselines`, `get_baseline` | Index lookup and resolved-path containment. |
| 11 | `backend/core/pipeline.py` | `baseline_features`, `nullable`, `analyze` | Orchestration, cache inputs, content-derived IDs, warnings, full-resolution detection and bounded chart data. |
| 12 | `backend/main.py` | route functions, `read_limited`, `execute`, `remember` | Multipart -> bounded read -> worker thread -> analysis -> bounded cache -> JSON; CPU lock and useful HTTP errors. |
| 13 | package `__init__.py` files | module boundaries | They establish importable packages; no hidden processing runs on import. |
| 14 | `backend/requirements*.txt` (core, alignment and browser) | core pins vs optional model environment | Why are large model dependencies optional and separately resolved? |

Trace this exact path on paper:

```text
POST /api/analyze
  -> validate baseline/transcript/files
  -> load_audio
  -> provided timing OR WhisperX OR explicit estimate
  -> baseline_features + extract_features
  -> word_measurements
  -> detect_flaws -> classify + explain
  -> score
  -> mapped chart series + reproducible ID
  -> AnalysisResult JSON
```

### Essential mathematical exercises

- Given baseline rate 3, participant rate 5, and scale 0.8: deviation = 2.5. With threshold 1.5, does it flag?
- Why would comparing the participant to a *global baseline mean* incorrectly flag expressive baseline words?
- Why does dividing every speaker's pitch by their own standard deviation erase monotone delivery? Centering semitones on the median retains relative range.
- Double every waveform amplitude. Why should relative volume differences remain nearly unchanged?
- A 3-second severe flaw in a 12-second speech contributes a 2.25-point penalty to its rubric dimension before rounding.
- Why are baseline and participant recording timestamps different, and how do corresponding words map them?

## 4. Read the dashboard in the order a user sees it

| Order | File | What to revise |
|---|---|---|
| 1 | `frontend/public/local.html` | HTML entry point, viewport, root element, stylesheet/module paths. |
| 2 | `frontend/public/dashboard.css` | variables, typography, grid, states, breakpoints, focus indicators, reduced motion. |
| 3 | `frontend/public/dashboard.js` | `escapeHtml`, `clock`, `scaffold`, `lineChart`, `radarChart`, `mountDashboard`. |
| 4 | `frontend/app/layout.tsx` | Next metadata and shared stylesheet. |
| 5 | `frontend/app/page.tsx` | React lifecycle mounts the shared dashboard and cleans up on unmount. |
| 6 | `frontend/next.config.ts` | standalone server output. |
| 7 | `frontend/tsconfig.json`, `frontend/next-env.d.ts` | TypeScript/framework declarations. |
| 8 | `frontend/package.json` | dev, build, start and typecheck commands and package pins. |

Inside `mountDashboard`, revise in this order:

1. State, DOM lookup, event registration, AbortController, backend fetch/error handling.
2. Baseline selection and same-text loading.
3. Upload form -> FormData -> backend result.
4. Controlled fixture buttons -> prebuilt variant analysis.
5. `render`: scores, warnings, playback, charts, explanation cards and highlighted words.
6. `drawWaveform` + `loadWaveform`: decode actual audio and draw peaks; they do not invent waveform values.
7. `seekAndPlay` and time updates: seek the participant, stop at region end, highlight the active words/cards.
8. Export: download the exact report JSON.
9. Cleanup: abort requests, disconnect ResizeObserver, stop playback, close AudioContext, revoke object URLs.

Exercise: follow a click on "Severe changes" into `/api/demo`, then back through `render`. Follow "Play this section" into the audio player. Explain why transcript text must be escaped before inserting HTML. The Canvas has audio controls as an accessible alternative; SVG charts currently have descriptive labels rather than a detailed data-table alternative.

## 5. Verify the behavior

Read `tests/test_pipeline.py`, `pytest.ini`, `scripts/evaluate.py`, and `scripts/check_dashboard.py`. Tests cover expected behavior, not just whether functions execute.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.validate_dataset
.\.venv\Scripts\python.exe -m scripts.evaluate
node --check frontend/public/dashboard.js
```

Read `reports/evaluation.json`. Explain prediction precision, label recall, matching policy, IoU and boundary error. A fragmented pacing detection can overlap one global pacing label; this evaluation explicitly pools those fragments for label coverage. Fixture metrics do not establish real speech accuracy.

For browser review: test uploads, invalid transcript errors, every severity button, playback, seek, export, narrow screens, and keyboard focus. For Next.js, run typecheck/build once npm is available; passing backend tests does not verify that shell.

## 6. Revise packaging and documentation

| Files | What to explain |
|---|---|
| `scripts/start.ps1` | local environment/bootstrap and loopback startup |
| `backend/Dockerfile` | core install, generated fixtures, FastAPI startup |
| `frontend/Dockerfile` | separate build/runtime stages and public backend URL |
| `docker-compose.yml` | default backend vs optional Next profile, healthcheck and ports |
| `.gitignore`, `.dockerignore` | exclude environments, caches, temporary reports and unreviewed media |
| `AGENTS.md` | persistent collaboration and accurate reporting rules |
| `docs/PRD.md` | requirements and submission obligations |
| `docs/TDD.md`, `docs/implementation_strategy.md` | original design and actual changes |
| `docs/task.md` | verified work vs open work |
| `docs/everythingyoushouldknow.md` | conceptual learning guide, with implementation corrections |
| `docs/TECHNICAL_REPORT.md`, `docs/TECHNICAL_REPORT.pdf`, `scripts/build_technical_report.py`, `docs/DEMO_SCRIPT.md` | technical methodology, bounded PDF export and video narrative |
| `docs/CODE_REVIEW_GUIDE.md` | this complete revision order |
| `README.md` | another person should be able to run the project from these instructions |

Generated folders (`.venv`, `.npm-cache`, `__pycache__`, `.pytest_cache`) are not code to memorize. Generated WAV files are for listening; JSON artifacts should be inspected with the scripts above. `problemstatement.pdf` is the original challenge reference.

## 7. A repeatable revision routine

**First pass:** Read the goal and draw the data flow. **Second pass:** Follow one audio file through every backend function. **Third pass:** Follow its JSON into the browser. **Fourth pass:** Run tests and explain one failure you would expect if a guard were removed. **Fifth pass:** Change one sensitivity value, compare the report, then restore it.

Keep four notes per source file: purpose, input/output, key logic/formula, and one edge case. This is more useful than memorizing every line. After each future implementation session, revise changed files first, their callers next, and relevant tests last.


## 8. Revise the frontend refresh (14 October 2026)

Read the changed files in this order:

| Order | File | What changed / questions to revise |
|---|---|---|
| 1 | `logo.png`, `frontend/public/cadence-logo.png` | User-supplied artwork and byte-identical web copy. Why are these URLs different on GitHub, FastAPI and Next.js? The original image was not edited. |
| 2 | `frontend/public/dashboard.css` | Charcoal/cyan design tokens, brand image framing, hero, navigation, process strip, practice room, upload states, score/profile/results, mobile breakpoints, reduced motion and loading state. Follow token -> selector -> breakpoint override. |
| 3 | `frontend/public/dashboard.js` | `logoUrl` resolves relative to `import.meta.url`, so both entry points load the same public asset. `icon` provides local SVG interface icons. `scaffold` preserves the API's form/control IDs while replacing the presentation. |
| 4 | `frontend/public/dashboard.js` interactions | Follow `updateFileLabel`, file/drop events, hero/empty-state actions, `setBusy`, `render`, warning disclosure, score meter, selected samples and `aria-pressed` feature buttons. Trace the existing playback/export paths afterward. |
| 5 | `frontend/public/local.html` | Local title, description, theme color, favicon/apple icon, branded loading markup and JavaScript-disabled fallback. Assets use `/assets/` because FastAPI mounts that route. |
| 6 | `frontend/app/layout.tsx` | Matching title/description and PNG icon metadata; Next.js serves assets at the root. |
| 7 | `frontend/app/page.tsx` | Matching branded loading screen, then the existing shared controller mount and cleanup. |
| 8 | `README.md` | Supplied logo, run instructions and current styling notes. |
| 9 | `docs/task.md`, `docs/everythingyoushouldknow.md` | Current implementation/verification status and conceptual explanation. |

The empty-state waveform illustration is decorative HTML/CSS and is not audio evidence. Actual report waveforms still come from decoded recordings. Fixture provenance and approximate-timing notices remain visible; important quality notes expand automatically for synthetic, approximate or weak-voicing results.

Useful revision commands from the project root:

```powershell
node --check frontend/public/dashboard.js
.\.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

Then review `http://127.0.0.1:8000`: navigation anchors, header/hero/footer logos, browser icon, file name display, every sample level, feature switching, warning expansion, playback/seek, transcript highlights and export. Check 390px, 680px, 820px and desktop widths, keyboard focus and reduced-motion settings.

Browser verification can be rerun using `.\.venv\Scripts\python.exe -m scripts.check_dashboard` when subprocess permissions allow it. The current attempt failed before browser launch. The supplied reference URL was also unavailable, so exact reference matching and visual layout are not verified. The Next.js shell still needs `npm install`, `npm run typecheck` and `npm run build` from `frontend` when package access is available.

Git handoff for this session uses the already configured `origin` and `main`: stage the changes, commit the redesign/logo integration, then `git push origin main`. No force push or remote replacement is needed.
