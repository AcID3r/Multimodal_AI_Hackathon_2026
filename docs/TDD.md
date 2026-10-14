# Technical Design Document (TDD)
# Contrastive Speech Analytics & Temporal Flaw Grounding System

**Version**: 1.0  
**Date**: October 12, 2026  
**Author**: Hackathon Team  
**Status**: Draft — Awaiting Approval

> Implementation update (2026-10-12): the local FastAPI dashboard and core are runnable. The optional Next.js shell is not build-verified. Reviewed real speeches and optional WhisperX inference remain open. See `docs/task.md`, `docs/TECHNICAL_REPORT.md`, and `docs/CODE_REVIEW_GUIDE.md` for the actual implementation. The detailed architecture below retains the original plan.

> Algorithm changes: matched-word participant-minus-baseline deltas replace global-mean comparison; median-centered semitones/relative dB preserve modulation; YIN plus periodicity gating replaces pYIN; Canvas/SVG replace WaveSurfer/Chart.js; supplied or explicitly estimated timings are available alongside the unverified WhisperX adapter. No calibrated statistical-significance claim is made.

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Upload   │  │  Waveform    │  │  Radar   │  │  Flaw Cards   │  │
│  │  Panel    │  │  Visualizer  │  │  Chart   │  │  + Causal     │  │
│  └──────────┘  └──────────────┘  └──────────┘  └───────────────┘  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ REST API (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI / Python)                    │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────────┐ │
│  │  Audio       │  │  Feature      │  │  Flaw Detection          │ │
│  │  Ingestion   │  │  Extraction   │  │  & Scoring Engine        │ │
│  │  Pipeline    │  │  Engine       │  │                          │ │
│  └──────┬───────┘  └───────┬───────┘  └──────────┬───────────────┘ │
│         │                  │                     │                  │
│  ┌──────▼───────┐  ┌───────▼───────┐  ┌──────────▼───────────────┐ │
│  │  Forced      │  │  MFCC, FFT,   │  │  Z-score deviation      │ │
│  │  Alignment   │  │  F0, Energy,  │  │  Temporal grounding      │ │
│  │  (whisperx)  │  │  Pause, Rate  │  │  Causal explanation gen  │ │
│  └──────────────┘  └───────────────┘  └──────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                       │
│  ┌──────────────────┐  ┌───────────────────────────────────────┐   │
│  │  Contrastive     │  │  Analysis Results (JSON)              │   │
│  │  Dataset (audio  │  │  - Features per segment               │   │
│  │  + transcripts   │  │  - Flaw regions with timestamps       │   │
│  │  + labels)       │  │  - Causal explanations                │   │
│  └──────────────────┘  └───────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Backend (Python)

| Component | Technology | Version | Justification |
|---|---|---|---|
| **Web Framework** | FastAPI | 0.100+ | Async, auto-docs, type-safe, fast |
| **Audio Processing** | librosa | 0.10+ | Industry standard for audio feature extraction |
| **Forced Alignment** | whisperx | latest | Best open-source forced alignment with word-level timestamps |
| **Speech-to-Text** | whisper (openai) | large-v3 | State-of-the-art transcription accuracy |
| **Signal Processing** | scipy | 1.11+ | FFT, signal filtering, statistical analysis |
| **Numerical Computing** | numpy | 1.24+ | Array operations, mathematical computations |
| **TTS for Flawed Speech** | Coqui TTS / edge-tts | latest | Free, controllable speech synthesis |
| **Audio I/O** | soundfile, pydub | latest | Read/write various audio formats |
| **Data Validation** | pydantic | 2.0+ | Request/response schema validation |

### 2.2 Frontend (JavaScript/TypeScript)

| Component | Technology | Version | Justification |
|---|---|---|---|
| **Framework** | Next.js (React) | 14+ | SSR, file routing, API routes, excellent DX |
| **Waveform Rendering** | WaveSurfer.js | 7+ | Best waveform visualization library with region support |
| **Charts** | Chart.js + react-chartjs-2 | 4+ | Radar charts, line charts, flexible and lightweight |
| **Styling** | CSS Modules + custom CSS | - | Maximum control, premium aesthetics |
| **HTTP Client** | fetch API | - | Built-in, no extra dependencies |
| **Audio Playback** | Web Audio API | - | Native browser audio with precise control |

### 2.3 Infrastructure

| Component | Technology | Justification |
|---|---|---|
| **Containerization** | Docker + docker-compose | Reproducibility across environments |
| **Python Env** | pip + requirements.txt | Simple, reproducible dependency management |
| **Node Env** | npm + package.json | Standard Node.js package management |

---

## 3. Data Model

### 3.1 Contrastive Dataset Schema

```
dataset/
├── metadata.json                    # Master index of all speech pairs
├── speeches/
│   ├── speech_001/
│   │   ├── info.json                # Speech metadata (speaker, source, topic)
│   │   ├── transcript.txt           # Raw text transcript
│   │   ├── ideal/
│   │   │   ├── audio.wav            # Original high-quality recording
│   │   │   └── alignment.json       # Word-level timestamps
│   │   ├── flawed_level_1/          # Egregiously bad
│   │   │   ├── audio.wav
│   │   │   ├── alignment.json
│   │   │   └── flaw_labels.json     # What flaws were injected, where
│   │   ├── flawed_level_2/          # Moderately bad
│   │   │   └── ...
│   │   └── flawed_level_3/          # Almost perfect (subtle flaws)
│   │       └── ...
│   ├── speech_002/
│   │   └── ...
```

### 3.2 Alignment JSON Schema

```json
{
  "words": [
    {
      "word": "Four",
      "start": 0.0,
      "end": 0.35,
      "confidence": 0.98
    },
    {
      "word": "score",
      "start": 0.36,
      "end": 0.72,
      "confidence": 0.97
    }
  ],
  "segments": [
    {
      "text": "Four score and seven years ago",
      "start": 0.0,
      "end": 2.5
    }
  ]
}
```

### 3.3 Flaw Label Schema

```json
{
  "speech_id": "speech_001",
  "flaw_level": 2,
  "flaw_regions": [
    {
      "id": "flaw_001",
      "type": "pacing_too_fast",
      "category": "pacing",
      "start_time": 3.2,
      "end_time": 5.8,
      "severity": 0.7,
      "description": "Speech rate increased to 5.2 syllables/sec vs baseline 3.1",
      "affected_words": ["and", "seven", "years", "ago", "our", "fathers"]
    }
  ]
}
```

### 3.4 Feature Extraction Output Schema

```json
{
  "speech_id": "speech_001",
  "variant": "flawed_level_2",
  "sample_rate": 16000,
  "duration_seconds": 45.3,
  "features": {
    "mfcc": {
      "values": [[...], [...], ...],
      "hop_length": 512,
      "n_mfcc": 13,
      "timestamps": [0.0, 0.032, 0.064, ...]
    },
    "f0": {
      "values": [120.5, 122.3, null, ...],
      "timestamps": [0.0, 0.01, 0.02, ...],
      "unit": "Hz"
    },
    "energy_rms": {
      "values": [0.023, 0.045, ...],
      "timestamps": [0.0, 0.032, ...],
      "unit": "amplitude"
    },
    "speech_rate": {
      "values": [3.2, 3.5, 4.1, ...],
      "window_size_seconds": 2.0,
      "timestamps": [1.0, 2.0, 3.0, ...],
      "unit": "syllables_per_second"
    },
    "pauses": [
      {"start": 5.2, "end": 5.8, "duration": 0.6},
      {"start": 12.1, "end": 12.3, "duration": 0.2}
    ]
  }
}
```

### 3.5 Analysis Result Schema (API Response)

```json
{
  "overall_score": 72,
  "rubric_scores": {
    "vocal_tone": 8,
    "pacing_rhythm": 5,
    "volume_dynamics": 7,
    "pause_usage": 6,
    "vocal_clarity": 8
  },
  "flaw_regions": [
    {
      "id": "flaw_001",
      "type": "pacing_too_fast",
      "category": "pacing",
      "start_time": 3.2,
      "end_time": 5.8,
      "severity": 0.7,
      "severity_label": "moderate",
      "transcript_segment": "and seven years ago our fathers",
      "causal_explanation": {
        "summary": "Speaking rate spiked to 5.2 syllables/sec, 68% faster than the baseline rate of 3.1 syllables/sec",
        "mathematical_detail": "σ-deviation = 2.3 from baseline mean speech rate. Energy RMS dropped 40% indicating mumbling under speed.",
        "recommendation": "Slow down in this section. The phrase 'seven years ago' carries historical weight and benefits from deliberate pacing around 3.0 syl/sec."
      },
      "feature_deltas": {
        "speech_rate": {"baseline": 3.1, "participant": 5.2, "z_score": 2.3},
        "energy_rms": {"baseline": 0.045, "participant": 0.027, "z_score": -1.8}
      }
    }
  ],
  "feature_timeseries": {
    "f0": {"baseline": [...], "participant": [...], "timestamps": [...]},
    "energy_rms": {"baseline": [...], "participant": [...], "timestamps": [...]},
    "speech_rate": {"baseline": [...], "participant": [...], "timestamps": [...]}
  }
}
```

---

## 4. Core Algorithms

### 4.1 Feature Extraction Pipeline

```python
# Pseudocode for feature extraction
def extract_features(audio_path, transcript_path):
    # 1. Load and preprocess audio
    audio, sr = librosa.load(audio_path, sr=16000)
    
    # 2. Forced alignment (word → timestamp mapping)
    alignment = whisperx.align(transcript, audio, sr)
    
    # 3. Extract acoustic features
    features = {
        "mfcc": librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13),
        "f0": librosa.pyin(audio, fmin=50, fmax=500),
        "energy_rms": librosa.feature.rms(y=audio),
        "spectral_centroid": librosa.feature.spectral_centroid(y=audio, sr=sr),
        "zcr": librosa.feature.zero_crossing_rate(audio),
    }
    
    # 4. Compute speech rate per segment
    features["speech_rate"] = compute_speech_rate(alignment, window_size=2.0)
    
    # 5. Detect pauses
    features["pauses"] = detect_pauses(audio, sr, min_pause_duration=0.15)
    
    # 6. Normalize for speaker-agnostic comparison
    features = speaker_normalize(features)
    
    return features, alignment
```

### 4.2 Flaw Detection via Z-Score Deviation

```python
def detect_flaws(baseline_features, participant_features, alignment):
    flaw_regions = []
    
    for feature_name in ["f0", "energy_rms", "speech_rate", "mfcc_distance"]:
        baseline = baseline_features[feature_name]
        participant = participant_features[feature_name]
        
        # Align time axes via DTW or forced alignment mapping
        aligned_baseline, aligned_participant = time_align(baseline, participant)
        
        # Compute z-scores
        mean_b, std_b = np.mean(aligned_baseline), np.std(aligned_baseline)
        z_scores = (aligned_participant - mean_b) / std_b
        
        # Find contiguous regions where |z| > threshold
        threshold = 1.5  # configurable
        flaw_mask = np.abs(z_scores) > threshold
        regions = find_contiguous_regions(flaw_mask, timestamps)
        
        for region in regions:
            flaw_regions.append({
                "type": classify_flaw(feature_name, z_scores[region]),
                "start_time": region.start,
                "end_time": region.end,
                "severity": compute_severity(z_scores[region]),
                "z_score": np.mean(np.abs(z_scores[region])),
                "feature_name": feature_name
            })
    
    # Merge overlapping flaw regions
    flaw_regions = merge_overlapping(flaw_regions)
    
    return flaw_regions
```

### 4.3 Speaker Normalization

```python
def speaker_normalize(features):
    """
    Z-score normalize pitch and energy to remove speaker-specific
    biological differences (deeper voice, louder natural volume, etc.)
    """
    # Normalize F0 (pitch) — removes gender/voice depth bias
    f0_values = features["f0"][~np.isnan(features["f0"])]
    features["f0_normalized"] = (features["f0"] - np.mean(f0_values)) / np.std(f0_values)
    
    # Normalize energy — removes microphone/volume bias
    energy = features["energy_rms"]
    features["energy_normalized"] = (energy - np.mean(energy)) / np.std(energy)
    
    # Speech rate is already speaker-agnostic (syllables/sec)
    
    return features
```

### 4.4 Causal Explanation Generation

```python
def generate_causal_explanation(flaw_region, baseline_features, participant_features):
    templates = {
        "pacing_too_fast": {
            "summary": "Speaking rate spiked to {p_rate:.1f} syl/sec, {pct:.0f}% faster than baseline {b_rate:.1f} syl/sec",
            "recommendation": "Slow down during '{transcript}'. This section benefits from deliberate pacing."
        },
        "pitch_monotone": {
            "summary": "Pitch variance dropped to {p_var:.1f} Hz² vs baseline {b_var:.1f} Hz². Voice became monotone.",
            "recommendation": "Add vocal variety in '{transcript}'. Vary pitch by ±{target_range:.0f} Hz for emphasis."
        },
        # ... more templates for each flaw type
    }
    
    template = templates[flaw_region["type"]]
    context = compute_context(flaw_region, baseline_features, participant_features)
    
    return {
        "summary": template["summary"].format(**context),
        "mathematical_detail": f"σ-deviation = {flaw_region['z_score']:.1f} from baseline distribution",
        "recommendation": template["recommendation"].format(**context)
    }
```

---

## 5. API Design

### 5.1 Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Upload audio + transcript, get full analysis |
| `GET` | `/api/analyze/{id}` | Get analysis results by ID |
| `GET` | `/api/baselines` | List available baseline speeches |
| `POST` | `/api/baselines/compare` | Compare participant audio against specific baseline |
| `GET` | `/api/health` | Health check |

### 5.2 POST /api/analyze — Request

```
Content-Type: multipart/form-data

Fields:
  - audio: File (.wav, .mp3, .flac)
  - transcript: File (.txt) [optional — auto-transcribe if missing]
  - baseline_id: string [optional — auto-select closest match]
```

### 5.3 POST /api/analyze — Response

```json
{
  "analysis_id": "uuid",
  "status": "complete",
  "duration_seconds": 45.3,
  "overall_score": 72,
  "rubric_scores": { ... },
  "flaw_regions": [ ... ],
  "feature_timeseries": { ... },
  "causal_explanations": [ ... ]
}
```

---

## 6. Frontend Architecture

### 6.1 Page Structure

```
pages/
├── index.js          # Landing page with upload form
├── analysis/
│   └── [id].js       # Analysis results dashboard
└── api/
    └── proxy.js      # API proxy to backend
```

### 6.2 Component Tree

```
<App>
├── <Header />
├── <UploadPanel>
│   ├── <AudioDropzone />
│   ├── <TranscriptInput />
│   └── <BaselineSelector />
├── <AnalysisDashboard>
│   ├── <ScoreOverview>
│   │   ├── <OverallScore />
│   │   └── <RubricRadarChart />
│   ├── <WaveformViewer>
│   │   ├── <WaveformCanvas />        # WaveSurfer.js
│   │   ├── <FlawRegionOverlay />
│   │   └── <PlaybackControls />
│   ├── <FeatureTimeSeries>
│   │   ├── <F0ComparisonChart />
│   │   ├── <EnergyComparisonChart />
│   │   └── <SpeechRateChart />
│   ├── <FlawCardsPanel>
│   │   └── <FlawCard>               # One per detected flaw
│   │       ├── <FlawHeader />
│   │       ├── <CausalExplanation />
│   │       └── <MathDetail />
│   └── <TranscriptView>
│       └── <HighlightedTranscript /> # Words colored by flaw severity
└── <Footer />
```

---

## 7. Performance Considerations

| Concern | Mitigation |
|---|---|
| Audio processing takes 10-30s | Show progress bar; process in background task |
| Large audio files | Limit to 10 min max; resample to 16kHz mono |
| Feature arrays are large | Downsample for visualization; full precision for analysis |
| Multiple feature extractions | Cache extracted features per audio file |
| Frontend rendering many data points | Use canvas-based rendering (WaveSurfer); decimate for charts |

---

## 8. Security Considerations

| Concern | Mitigation |
|---|---|
| File upload exploits | Validate file type, limit size (50MB max), scan with pydub |
| Path traversal | Sanitize all filenames, use UUID-based storage |
| API abuse | Rate limiting on upload endpoint |
| Data privacy | No persistent storage of uploaded audio (process & discard) |

---

## 9. Testing Strategy

### 9.1 Unit Tests
- Feature extraction functions (known audio → known features)
- Z-score computation correctness
- Flaw region detection against labeled data
- Causal explanation template rendering

### 9.2 Integration Tests
- End-to-end: upload audio → receive analysis JSON
- Frontend: upload flow → dashboard rendering

### 9.3 Stress Tests
- Process 10-minute audio without crash
- Handle edge cases: silence, noise-only, very fast speech
- Verify deterministic output across 3 runs (reproducibility)

---

## 10. Deployment Architecture

```
docker-compose.yml
├── backend (Python FastAPI)
│   ├── Port: 8000
│   ├── Volumes: ./dataset, ./temp_uploads
│   └── GPU: not required
├── frontend (Next.js)
│   ├── Port: 3000
│   └── Env: NEXT_PUBLIC_API_URL=http://localhost:8000
└── (optional) nginx reverse proxy
```
