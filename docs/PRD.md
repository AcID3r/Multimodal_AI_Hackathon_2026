# Product Requirements Document (PRD)
# Contrastive Speech Analytics & Temporal Flaw Grounding System

**Project**: Multimodal AI Hackathon 2026 — Track C  
**Version**: 1.0  
**Date**: October 12, 2026  
**Status**: Draft — Awaiting Approval

> Implementation update (2026-10-12): the local FastAPI dashboard and core are runnable. The optional Next.js shell is not build-verified. Reviewed real speeches and optional WhisperX inference remain open. See `docs/task.md`, `docs/TECHNICAL_REPORT.md`, and `docs/CODE_REVIEW_GUIDE.md` for the actual implementation. The detailed architecture below retains the original plan.

---

## 1. Executive Summary

We are building a **speech evaluation system** that can objectively analyze spoken performances by comparing them against "ideal" deliveries. The system uses audio signal processing, contrastive learning, and temporal analysis to pinpoint *exactly where* and *why* a speaker's delivery fails — then presents this via an interactive dashboard.

Think of it as a "Grammarly for public speaking" — but backed by real acoustic math, not vibes.

---

## 2. Problem Statement

### The Pain
- **Subjective judging**: Speech competitions (debate, oratory, interpretive reading) rely on human judges who score inconsistently.
- **Vague feedback**: Participants hear "work on your tone" but never learn *where* in their speech the tone failed, or *what* the mathematical deviation was.
- **No contrastive dataset exists**: Datasets exist for speech recognition (STT), but none map good rhetorical delivery vs. bad delivery of the *same text*.

### The Opportunity
Build a system that:
1. Creates a contrastive dataset of ideal vs. intentionally-flawed speeches
2. Extracts rich acoustic features (FFT, MFCCs, pitch, F0, pauses, speech rate)
3. Temporally grounds flaw regions to exact timestamps
4. Explains *why* each flaw is a flaw using causal math explanations
5. Renders everything via an interactive dashboard

---

## 3. Target Users

| User Type | Need |
|---|---|
| **Speech competitors** | Objective, actionable feedback on delivery |
| **Debate coaches** | Data-backed insights to guide student practice |
| **Public speaking trainers** | Scalable evaluation tool across many students |
| **Hackathon judges** | A working, impressive, well-documented prototype |

---

## 4. Core Features & Requirements

### 4.1 Custom Contrastive Dataset (Weight: 30% of evaluation)

| ID | Requirement | Priority |
|---|---|---|
| D-1 | Source ≥5 high-quality "ideal" speech recordings (TED talks, famous orations, champion debaters) | P0 |
| D-2 | Transcribe all ideal speeches accurately | P0 |
| D-3 | Generate "flawed" versions of each speech using TTS with injected delivery flaws | P0 |
| D-4 | Build a gradient from "egregiously bad" → "almost perfect" (minimum 3 flaw levels per speech) | P0 |
| D-5 | Temporally label all paired recordings with alignment timestamps | P0 |
| D-6 | Document dataset construction methodology | P0 |
| D-7 | Host dataset on GitHub or public Google Drive with link in README | P0 |

**Flaw categories to inject:**
- Monotone delivery (flat pitch)
- Wrong pacing (too fast / too slow)
- Misplaced pauses (breaking rhetorical flow)
- Volume inconsistency (too loud / too quiet at wrong moments)
- Filler words injection ("um", "uh", "like")
- Vocal fry / creaky voice

### 4.2 Feature Extraction & Forced Alignment (Weight: 20%)

| ID | Requirement | Priority |
|---|---|---|
| F-1 | Perform forced alignment mapping transcript → audio timestamps | P0 |
| F-2 | Extract MFCCs (Mel-Frequency Cepstral Coefficients) | P0 |
| F-3 | Extract F0 (fundamental frequency) contours | P0 |
| F-4 | Compute speech rate (syllables/second per segment) | P0 |
| F-5 | Detect and measure pause intervals | P0 |
| F-6 | Extract energy/RMS contours | P0 |
| F-7 | Compute spectral features via FFT | P1 |
| F-8 | Normalize all features for speaker-agnostic comparison | P0 |

### 4.3 Temporal Grounding & Causal Flaw Extraction (Weight: 25%)

| ID | Requirement | Priority |
|---|---|---|
| T-1 | Compare participant features against baseline features at aligned time segments | P0 |
| T-2 | Detect statistically significant deviations (z-score or similar) | P0 |
| T-3 | Isolate exact start/end timestamps of each flaw region | P0 |
| T-4 | Classify flaw type (pacing, pitch, pause, volume, clarity) | P0 |
| T-5 | Generate structured causal explanations linking math delta → human-readable explanation | P0 |
| T-6 | Produce per-rubric scores (1-10 scale) for each evaluation dimension | P0 |

### 4.4 Interactive Dashboard (Weight: 15%)

| ID | Requirement | Priority |
|---|---|---|
| V-1 | Accept audio file upload (.wav, .mp3) | P0 |
| V-2 | Accept transcript upload (.txt) or auto-transcribe | P0 |
| V-3 | Display waveform visualization with flaw regions highlighted | P0 |
| V-4 | Render time-series overlays comparing baseline vs. participant for each feature | P0 |
| V-5 | Show causal explanation cards for each detected flaw region | P0 |
| V-6 | Display rubric-based scoring radar chart | P0 |
| V-7 | Allow audio playback with synchronized flaw highlighting | P1 |
| V-8 | Responsive, visually polished design | P0 |

### 4.5 Reproducibility & Code Quality (Weight: 10%)

| ID | Requirement | Priority |
|---|---|---|
| R-1 | Docker or clear pip/npm install instructions | P0 |
| R-2 | Deterministic results across runs (seeded randomness) | P0 |
| R-3 | Clean code architecture (separated concerns) | P0 |
| R-4 | Comprehensive README with setup + usage | P0 |

---

## 5. Expected Deliverables (from problem statement)

| Deliverable | Status |
|---|---|
| GitHub repository with full codebase + docs | 🔲 TODO |
| Custom contrastive dataset (in repo or Google Drive link) | 🔲 TODO |
| Interactive dashboard (web-based prototype) | 🔲 TODO |
| Technical documentation (max 6 pages) | 🔲 TODO |
| 3-10 min YouTube demo video | 🔲 TODO |

---

## 6. Success Metrics

| Metric | Target |
|---|---|
| Flaw detection precision | ≥ 80% of injected flaws detected |
| Temporal grounding accuracy | Within ±0.5s of actual flaw boundaries |
| Dashboard load time | < 3 seconds for analysis results |
| Reproducibility | Same input → same output across 3 runs |
| Evaluation score coverage | All 5 rubric dimensions addressed |

---

## 7. Constraints & Assumptions

- **Time constraint**: Hackathon timeline (limited days)
- **No GPU required**: All processing should run on CPU (no deep learning training during demo)
- **Open-source tools only**: All libraries must be freely available
- **Browser-based dashboard**: Must run in a standard web browser
- **Speaker-agnostic**: Must normalize for different voice characteristics

---

## 8. Out of Scope (for v1)

- Real-time live speech evaluation
- Multi-language support (English only for v1)
- Training a custom deep learning model from scratch
- Mobile app
- User authentication / multi-user support
