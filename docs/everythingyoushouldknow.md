# Everything You Should Know 🧠
## A Complete Guide to Our Speech Analytics System — Explained Simply

**Last Updated**: October 12, 2026  
**Update Policy**: This file is updated every time we make a change to the project.

---

## Table of Contents

0. [🗺️ How to Read This Project (File-by-File Reading Order)](#0-️-how-to-read-this-project-file-by-file-reading-order)
1. [What Are We Building?](#1-what-are-we-building)
2. [The Problem We're Solving](#2-the-problem-were-solving)
3. [How Our System Works (The Big Picture)](#3-how-our-system-works-the-big-picture)
4. [The Contrastive Dataset — Our Secret Sauce](#4-the-contrastive-dataset--our-secret-sauce)
5. [Audio Feature Extraction — What the Computer "Hears"](#5-audio-feature-extraction--what-the-computer-hears)
6. [Forced Alignment — Matching Words to Sound](#6-forced-alignment--matching-words-to-sound)
7. [Flaw Detection — Finding Where Things Go Wrong](#7-flaw-detection--finding-where-things-go-wrong)
8. [Scoring & Causal Explanations](#8-scoring--causal-explanations)
9. [The Dashboard — Making It All Visual](#9-the-dashboard--making-it-all-visual)
10. [Technology Choices — Why We Picked What We Picked](#10-technology-choices--why-we-picked-what-we-picked)
11. [Alternatives We Considered (And Why We Said No)](#11-alternatives-we-considered-and-why-we-said-no)
12. [Glossary — Big Words Made Simple](#12-glossary--big-words-made-simple)
13. [Change Log](#13-change-log)

---

## 0. How to read the implemented project

The complete, current file-by-file roadmap is [CODE_REVIEW_GUIDE.md](CODE_REVIEW_GUIDE.md). It covers every source module, function, dataset artifact, frontend entry point, test, packaging file, and revision exercise. Follow that guide instead of the originally proposed file names.

Read in this order: problem statement and PRD -> task tracker and README -> dataset builder/metadata/labels -> configuration and schemas -> audio/alignment/features -> classification/explanation/detection/scoring -> dataset access/pipeline/API -> shared dashboard HTML/CSS/JS -> optional Next shell -> behavioral tests/evaluation -> startup/containers -> technical PDF and demo script.

### What actually works today

- FastAPI local dashboard, same-text uploads, feature extraction, corresponding-word comparisons, deterministic explanations and five rubric scores.
- Five controlled harmonic fixture groups, each with three severities, exact generated anchors, labels and provenance. These are tones, not human speeches.
- Seventeen behavioral tests pass; three repeated analyses have identical JSON.
- SVG feature/radar charts, Canvas waveform, playback and highlighted transcript are implemented in shared browser code. Full browser interaction/layout verification is still blocked.
- Five-page technical PDF and source shortlist exist. Real recordings, optional models, Next build, container runtime and external submission deliverables remain pending.

### Corrections to the conceptual planning notes below

Pitch is centered in semitones, not standardized to unit variance, so reduced pitch variation remains detectable. Relative dB removes overall gain while retaining local emphasis. We compare matched participant and baseline measurements, not the participant against a global baseline mean. The default 1.5 threshold is a tunable heuristic; it does **not** imply 87% detection accuracy or statistical significance. YIN with voiced gating is the current pitch extractor. Spectral/MFCC differences do not independently prove clarity or rhetorical richness. Thirteen MFCCs are a conventional engineering choice, not a universal guarantee that additional coefficients cannot help. Approximate timing is explicitly disclosed and does not meet precise forced-alignment requirements.

The remaining educational sections explain the original concepts. Use the technical report and code review guide for current algorithms, actual files and verified capabilities.

---

## 1. What Are We Building?

Imagine you're in a speech competition. You give a speech, and a judge gives you a score like 7/10. You ask "why?" and they say "your tone was off." But... *where* was it off? *How* was it off? They can't really explain it in numbers.

**We're building a computer system that can:**
- Listen to your speech 🎤
- Compare it to a great version of the same speech 🏆
- Find the exact moments where your delivery went wrong ❌
- Explain *why* it went wrong using math 📊
- Show you everything on a beautiful interactive dashboard 🖥️

It's like having a super-precise speech coach that never gets tired and always explains their reasoning with data.

---

## 2. The Problem We're Solving

### Why is this hard?

When a human judge evaluates a speech, they use their *feelings* and *experience*. Two judges can watch the same speech and give different scores. This is called **subjectivity**.

**Real-world example:**
- Judge A thinks your pause at 0:45 was "dramatic and powerful" → gives you 8/10
- Judge B thinks that same pause was "too long and awkward" → gives you 5/10

Same speech. Same moment. Different scores. That's the problem.

### What makes our solution special?

We use **math** instead of feelings. Instead of asking "does this *feel* right?", we ask:
- "Is the pitch here 2.3 standard deviations away from what a great speaker does?" 
- "Is the speaking speed 68% faster than the ideal speed for this part of the speech?"

Numbers don't have opinions. Numbers are the same every time you calculate them.

---

## 3. How Our System Works (The Big Picture)

Think of it like a 4-step process:

```
Step 1: LISTEN          Step 2: MEASURE         Step 3: COMPARE         Step 4: SHOW
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Upload your  │     │ Extract features │     │ Find where your  │     │ Beautiful    │
│ speech audio │ ──▶ │ (pitch, speed,   │ ──▶ │ speech differs   │ ──▶ │ dashboard    │
│ + transcript │     │  volume, pauses) │     │ from the ideal   │     │ with scores  │
└──────────────┘     └──────────────────┘     └──────────────────┘     └──────────────┘
```

### Why this order?

Each step depends on the one before it:
- You can't **measure** if you don't have audio to listen to
- You can't **compare** if you haven't measured anything yet
- You can't **show** results if you haven't done the comparison

It's like cooking: you can't bake a cake before mixing the ingredients, and you can't mix ingredients before buying them.

---

## 4. The Contrastive Dataset — Our Secret Sauce

### What is a "contrastive dataset"?

"Contrastive" means **comparing opposites**. Imagine lining up photos of clean rooms and messy rooms side by side. That's a contrastive dataset for room cleanliness.

We do the same for speeches:
- **"Ideal" version**: A famous speaker delivering a speech beautifully
- **"Flawed" versions**: The *same words* spoken badly in different ways

### Why do we need this?

The computer needs to learn what "good" sounds like before it can tell you what "bad" sounds like. It's like learning — you need to see examples of correct answers before you can spot wrong ones.

### How do we make flawed versions?

We use a technique called **TTS (Text-to-Speech)** — the computer reads the same transcript but we tell it to read it *wrong* on purpose:
- **Monotone**: Like a robot, no emotion (flat pitch)
- **Too fast**: Like someone rushing through a presentation
- **Too slow**: Like someone who forgot what they're saying
- **Wrong pauses**: Stopping at weird places mid-sentence

We make 3 levels of "bad":
1. 🔴 **Level 1 — Really bad**: Multiple obvious problems
2. 🟡 **Level 2 — Somewhat bad**: One or two noticeable issues
3. 🟢 **Level 3 — Almost perfect**: Very subtle mistakes (hard to catch)

### Why 3 levels?

Because "bad" isn't just one thing. A speech can be slightly off or completely terrible. Having 3 levels helps the system understand the *gradient* of quality — like grades in school (A, B, C, D, F).

### Why did we choose TTS for generating flawed speech?

**What we chose**: Microsoft's `edge-tts` (free text-to-speech with SSML control)

**Why**: 
- It's free (no API costs)
- We can precisely control pitch, speed, and volume using SSML tags
- It produces decent quality audio
- We can reproduce exactly the same flawed version every time

**Alternatives we considered**:
| Alternative | Why we said no |
|---|---|
| Self-recording flawed speeches | Too slow for hackathon; hard to be consistently "bad" on purpose; not reproducible |
| Google Cloud TTS | Costs money; requires API key setup; similar quality |
| Amazon Polly | Costs money; similar capability |
| Programmatically distorting real audio | Would try this as a supplement — stretching/compressing real audio for speed changes |
| Coqui TTS (open source) | Heavier to set up; more complex; edge-tts is simpler for our needs |

---

## 5. Audio Feature Extraction — What the Computer "Hears"

Humans hear "a nice voice" or "a boring tone." Computers hear numbers. We need to convert sound into numbers that capture *what makes a speech sound good or bad*.

### The Features We Extract

#### 🎵 F0 (Fundamental Frequency / Pitch)
**Simple explanation**: How high or low your voice sounds.  
**Why it matters**: Great speakers vary their pitch — going up for questions, down for statements, high for excitement. A monotone speaker stays flat.  
**How we measure it**: Using an algorithm called `pYIN` that tracks the fundamental frequency over time.  
**Unit**: Hertz (Hz). A typical male voice is 85-180 Hz. Female voice is 165-255 Hz.

#### 📊 MFCCs (Mel-Frequency Cepstral Coefficients)
**Simple explanation**: A compact "fingerprint" of what a voice sounds like at any moment.  
**Think of it like**: A recipe that captures the "flavor" of the voice — is it nasal? breathy? clear? resonant?  
**Why it matters**: MFCCs capture the overall tonal quality. A great speaker has rich, varied MFCCs. A poor speaker has repetitive, flat ones.  
**How many**: We use 13 coefficients per time frame (standard practice in speech science).  

**Why 13?** Research shows that 13 MFCCs capture enough information about the speech signal without being redundant. Using more doesn't help much; using fewer loses important detail.

#### ⚡ Energy (RMS — Root Mean Square)
**Simple explanation**: How loud the speech is at any given moment.  
**Why it matters**: Great speakers use volume for emphasis — getting louder on important words, softer for suspense. Poor speakers either mumble or shout uniformly.  
**How we measure it**: Calculate the RMS (average power) of the audio signal in small windows.

#### 🏃 Speech Rate
**Simple explanation**: How many syllables per second someone speaks.  
**Why it matters**: Too fast = audience can't follow. Too slow = audience gets bored. Great speakers speed up for excitement and slow down for emphasis.  
**How we measure it**: Count syllables (from the transcript alignment) per time window.  
**Normal range**: 3-5 syllables/second for English public speaking.

#### ⏸️ Pauses
**Simple explanation**: Moments of silence between words or phrases.  
**Why it matters**: Pauses are powerful tools. A well-placed pause after "I have a dream..." lets the words sink in. A bad pause mid-sentence ("I have... a dream") is awkward.  
**How we measure it**: Detect segments where audio energy drops below a threshold for >150ms.

#### 🌈 Spectral Features (FFT — Fast Fourier Transform)
**Simple explanation**: Breaking sound into its component frequencies — like splitting white light through a prism into a rainbow.  
**Why it matters**: Shows us the "color" of the voice at each moment. A clear voice has strong, focused frequencies. A muffled voice has scattered ones.  
**How we measure it**: Apply FFT to convert time-domain audio into frequency-domain representation.

### Why these specific features?

| Feature | What it captures | Why it's important for speech quality |
|---|---|---|
| F0 | Pitch variation | Monotone vs. expressive delivery |
| MFCCs | Voice quality/timbre | Overall vocal richness |
| Energy | Volume dynamics | Emphasis and dramatic range |
| Speech rate | Pacing | Too fast, too slow, or just right |
| Pauses | Silence placement | Rhetorical effectiveness |
| Spectral | Frequency balance | Vocal clarity and resonance |

**Alternatives we didn't use**:
| Feature | Why we skipped it |
|---|---|
| Jitter (pitch perturbation) | Too granular; more useful for detecting vocal disorders than speech quality |
| Shimmer (amplitude perturbation) | Same reason as jitter |
| Formants (F1, F2, F3) | More relevant for vowel quality / accent analysis, not speech delivery |
| Chromagram | Designed for music, not speech |

---

## 6. Forced Alignment — Matching Words to Sound

### What is forced alignment?

Imagine you have:
- An audio recording of "Four score and seven years ago"
- The text transcript: "Four score and seven years ago"

**Forced alignment** tells you EXACTLY when each word starts and ends in the audio:
- "Four" → starts at 0.0s, ends at 0.35s
- "score" → starts at 0.36s, ends at 0.72s
- "and" → starts at 0.73s, ends at 0.85s
- ... and so on

### Why do we need this?

Without alignment, we know your pitch was weird at timestamp 3.2 seconds, but we can't tell you *which word* you were saying at that moment. With alignment, we can say: "When you said the word 'freedom' at 3.2s, your pitch dropped unexpectedly."

This is what makes our feedback **actionable** instead of vague.

### Tool: WhisperX

**What we chose**: WhisperX (an extension of OpenAI's Whisper)

**Why WhisperX?**
- Gives us **word-level timestamps** (not just sentence-level)
- Built on Whisper, which is the most accurate speech-to-text model
- Open source and free
- Works on CPU (no GPU needed)

**Alternatives we considered**:
| Tool | Pros | Why we didn't pick it |
|---|---|---|
| Montreal Forced Aligner (MFA) | Very accurate alignment | Complex setup, requires pre-trained acoustic models, slower |
| Gentle | Simple API | Less accurate, fewer languages, hasn't been updated recently |
| Whisper (without X) | Great transcription | Only gives sentence-level timestamps, not word-level |
| Google Cloud Speech-to-Text | Very accurate | Costs money, requires API key, not offline |
| wav2vec2 + CTC alignment | State of the art | Much more complex to implement; WhisperX wraps similar tech more simply |

---

## 7. Flaw Detection — Finding Where Things Go Wrong

### The Core Idea: Z-Scores

This is the math heart of our system. Let me explain it simply.

**Imagine you're measuring the height of 100 kids in a class.**
- Average height: 140 cm
- Most kids are between 130-150 cm
- A kid who is 160 cm is "unusually tall"
- A kid who is 120 cm is "unusually short"

A **z-score** tells you *how unusual* a value is compared to the average:
- z-score of 0 = exactly average
- z-score of 1 = somewhat above average
- z-score of 2 = very above average (unusual)
- z-score of -2 = very below average (unusual)

**In our system**: We measure the "average" from the ideal speech (baseline), then check how far the participant's speech deviates at each moment.

```
Example:
Baseline speech rate at timestamp 3.2s: 3.1 syllables/sec (μ = 3.1, σ = 0.8)
Participant speech rate at 3.2s: 5.2 syllables/sec

z-score = (5.2 - 3.1) / 0.8 = 2.625

That's very high! → FLAG as "pacing_too_fast" 🚩
```

### What's the threshold?

We use |z| > 1.5 as our threshold. Why?

| Threshold | Meaning | Trade-off |
|---|---|---|
| |z| > 1.0 | Flag anything slightly unusual | Too many false alarms — would flag normal variation |
| **|z| > 1.5** | **Flag moderately unusual deviations** | **Good balance — catches real flaws, ignores noise** |
| |z| > 2.0 | Only flag very unusual things | Would miss subtle but real flaws |
| |z| > 3.0 | Only flag extreme outliers | Would miss most flaws entirely |

We picked **1.5** because it catches about 87% of truly different segments while ignoring random variation. This is configurable — users can adjust sensitivity.

### How do we find contiguous flaw regions?

We don't want to report "flaw at 3.2s" and "flaw at 3.25s" and "flaw at 3.3s" separately. They're all part of the same problem! We **merge** nearby flagged points into contiguous regions:

```
Individual flags:  ....XXXXX.XX.XXXXX....
After merging:     ....XXXXXXXXXXXXXXXXX....
                        ^start         ^end
                   One flaw region: 3.2s → 5.8s
```

### Why Z-scores instead of other methods?

| Method | What it does | Why we didn't choose it |
|---|---|---|
| **Z-score** ✅ | Measures how many standard deviations from the mean | Simple, interpretable, well-understood, explainable |
| Machine Learning classifier | Train a model to detect "good" vs "bad" | Need lots of labeled training data (we don't have enough for a hackathon) |
| DTW (Dynamic Time Warping) distance | Measures similarity between two time series | Good for overall similarity but doesn't tell you WHERE the difference is |
| Simple threshold (absolute values) | "Pitch above 200 Hz is bad" | Doesn't work across different speakers (some people naturally have higher voices) |
| Cosine similarity | Measures angle between feature vectors | Doesn't capture magnitude differences well |

**Z-scores win** because they are:
1. **Speaker-agnostic** (we normalize first, so z-scores work regardless of voice type)
2. **Interpretable** ("2.3 standard deviations above average" means something concrete)
3. **Temporal** (we can compute them at every time point)
4. **Explainable** (we can tell the user exactly HOW different they are, in numbers)

---

## 8. Scoring & Causal Explanations

### Rubric-Based Scoring

We score speeches on 5 dimensions, each 1-10:

| Dimension | What it measures | Features used |
|---|---|---|
| **Vocal Tone** | Expressiveness and pitch variation | F0 variance, F0 range, MFCCs |
| **Pacing/Rhythm** | Speed control and rhythmic flow | Speech rate, rate variance |
| **Volume Dynamics** | Appropriate loudness variation | Energy RMS, energy range |
| **Pause Usage** | Strategic use of silence | Pause count, duration, placement |
| **Vocal Clarity** | Crispness and articulation | Spectral features, MFCC stability |

### How Scores are Calculated

```
Score = 10 - (penalty_from_flaws_in_this_dimension)

Where penalty = Σ (severity × weight) for each flaw in this dimension

severity is calculated from the z-score:
- |z| 1.5-2.0 → severity 0.3 (minor)
- |z| 2.0-3.0 → severity 0.6 (moderate)
- |z| > 3.0 → severity 1.0 (severe)
```

### Causal Explanations

This is the "why" part. For each flaw, we generate THREE things:

1. **Summary** (one sentence, plain English):  
   > "Your speaking rate jumped to 5.2 syllables/second, 68% faster than the ideal pace of 3.1 syllables/second."

2. **Mathematical Detail** (for the technical audience):  
   > "σ-deviation = 2.3 from baseline mean speech rate (μ=3.1, σ=0.8). Energy RMS simultaneously dropped 40%, consistent with mumbling under increased speed."

3. **Recommendation** (what to actually do about it):  
   > "Slow down during 'and seven years ago our fathers'. This phrase carries historical weight and benefits from deliberate pacing around 3.0 syllables/sec."

### Why template-based explanations instead of AI-generated?

| Approach | Pros | Cons |
|---|---|---|
| **Template-based** ✅ | Reproducible (same input → same output), fast, no API costs, always correct | Less creative, might feel formulaic |
| LLM-generated (GPT-4, etc.) | More natural language, creative phrasing | Non-deterministic (different each run), costs money, might hallucinate, slow |

We chose **templates** because the hackathon explicitly requires **reproducibility** (10% of grade). If we used an LLM, the same speech could get different feedback each time. Templates guarantee identical output.

---

## 9. The Dashboard — Making It All Visual

### What the Dashboard Shows

1. **Upload Panel**: Drag-and-drop your audio file + paste your transcript
2. **Score Overview**: Big animated number (overall score) + radar chart (5 rubric scores)
3. **Waveform Viewer**: Sound wave with red highlighted regions = flaws
4. **Feature Comparison Charts**: Line graphs showing your speech vs. the ideal speech
5. **Flaw Cards**: Detailed cards for each detected flaw with explanations
6. **Transcript View**: Your speech text with problem words highlighted in colors

### Why a Web Dashboard?

| Option | Why we chose/didn't choose |
|---|---|
| **Web app (browser)** ✅ | Universal — works on any device with a browser. Easy to demo. Modern look possible. |
| Desktop app (Electron) | More work to build, harder to demo, judges need to install it |
| Jupyter notebook | Too technical, not "interactive dashboard", ugly |
| Command-line tool | Not visual at all, impossible to impress judges |
| Mobile app | Too complex for hackathon, not required |

### Why Next.js?

| Framework | Why we chose/didn't choose |
|---|---|
| **Next.js** ✅ | React-based (huge ecosystem), file-based routing, server-side rendering, great DX, easy API routes |
| Plain HTML/CSS/JS | Too primitive for a complex dashboard, no component reuse |
| Vue.js / Nuxt | Good but smaller ecosystem; React has more charting/audio libraries |
| Svelte / SvelteKit | Excellent performance but fewer audio visualization libraries |
| Angular | Too heavy/complex for a hackathon project |
| Streamlit (Python) | Easy but very limited styling, looks generic, hard to customize |

### Why WaveSurfer.js for Waveforms?

| Library | Why we chose/didn't choose |
|---|---|
| **WaveSurfer.js** ✅ | Purpose-built for waveform display, supports regions/markers, audio playback, plugin system, well-maintained |
| Peaks.js | Good but less flexible for custom regions |
| Custom Canvas rendering | Way too much work to build from scratch |
| D3.js | Powerful but generic — would need to build waveform rendering from scratch |

### Why Chart.js for Charts?

| Library | Why we chose/didn't choose |
|---|---|
| **Chart.js** ✅ | Simple, lightweight, supports radar/line/bar charts, great React integration |
| D3.js | More powerful but massive learning curve, overkill for our needs |
| Recharts | Good React integration but radar chart support is limited |
| Plotly.js | Heavy, more for data science dashboards |
| Victory | Good but less popular, fewer examples |

---

## 10. Technology Choices — Why We Picked What We Picked

### Backend: Python + FastAPI

**Why Python?**
- All the best audio/ML libraries are in Python (librosa, whisper, scipy)
- We know it well
- Fast development speed

**Why FastAPI specifically?**
| Feature | FastAPI | Flask | Django | Express.js |
|---|---|---|---|---|
| Speed | ⚡ Async, fast | Sync, slower | Heavy | Fast but wrong ecosystem |
| Auto-docs (Swagger) | ✅ Built-in | ❌ Manual | ❌ Manual | ❌ Manual |
| Type safety | ✅ Pydantic | ❌ | Partial | ❌ |
| File uploads | ✅ Easy | ✅ | ✅ | ❌ Python libs needed |
| Learning curve | Low | Low | High | Low but Python libs unavailable |
| **Verdict** | **✅ Best fit** | Good backup | Overkill | Wrong language |

### Audio Processing: librosa

**Why librosa?**
- The #1 Python library for audio analysis
- Has every feature we need (MFCC, F0, RMS, spectral features)
- Extremely well-documented
- Used by researchers worldwide

**Why not alternatives?**
| Library | Why we didn't choose |
|---|---|
| torchaudio | Requires PyTorch (heavy); we don't need deep learning |
| soundfile | Good for I/O but doesn't do feature extraction |
| pyAudioAnalysis | Less maintained, fewer features than librosa |
| essentia | Good but less Pythonic API, harder to learn quickly |

### Containerization: Docker

**Why Docker?**
- Hackathon requires **reproducibility** (10% of grade)
- "Works on my machine" → "Works on EVERY machine"
- One command to start everything: `docker-compose up`

---

## 11. Alternatives We Considered (And Why We Said No)

### The "Use a Pre-trained Model" Approach
**Idea**: Fine-tune a deep learning model (like wav2vec2) to classify speech quality.

**Why we said no**:
- Need lots of labeled training data (we're building the dataset from scratch — it'll be small)
- Training takes GPU time we may not have
- Black box — can't explain WHY something is a flaw (the hackathon values "causal explainability" at 25%)
- Not reproducible without exact model weights

### The "Just Use GPT-4 Audio" Approach
**Idea**: Send audio to GPT-4o and ask it to evaluate the speech.

**Why we said no**:
- Not reproducible (LLM outputs vary between runs)
- Can't provide mathematical rationale (just gives opinions)
- Costs money per API call
- Doesn't do temporal grounding (can't tell you exact timestamps)
- The hackathon is testing our ability to do signal processing, not just call an API

### The "Real-Time Streaming" Approach
**Idea**: Analyze speech in real-time as it's being delivered.

**Why we said no**:
- Way more complex (WebSocket streaming, buffered processing)
- Not required by the problem statement
- Harder to demo (need live speaker)
- Can save this as a future feature

---

## 12. Glossary — Big Words Made Simple

| Term | Simple Explanation |
|---|---|
| **Contrastive** | Comparing two opposite things side by side (good vs. bad) |
| **Temporal Grounding** | Pinpointing WHEN something happens (exact timestamps) |
| **Causal Explainability** | Explaining WHY something happened (not just WHAT) |
| **F0 / Fundamental Frequency** | The pitch of your voice — how high or low it sounds |
| **MFCC** | A mathematical "fingerprint" of what your voice sounds like |
| **FFT (Fast Fourier Transform)** | Breaking a sound wave into its component frequencies |
| **RMS (Root Mean Square)** | A way to measure "average loudness" |
| **Z-score** | How many "standard deviations" away from average something is |
| **Forced Alignment** | Matching each word in a transcript to its exact timestamp in audio |
| **TTS (Text-to-Speech)** | Computer reading text out loud |
| **SSML** | Special code that tells TTS HOW to read (fast, slow, loud, quiet) |
| **Baseline** | The "ideal" version we compare against |
| **Rubric** | A scoring guide with specific categories |
| **pYIN** | An algorithm for detecting pitch in audio (probabilistic YIN) |
| **DTW (Dynamic Time Warping)** | A technique to align two sequences that may be different speeds |
| **Spectral Centroid** | The "center of gravity" of a sound's frequency content |
| **Speaker-Agnostic** | Works regardless of who's speaking (male, female, deep voice, high voice) |
| **API** | A way for the frontend and backend to talk to each other over the internet |
| **FastAPI** | A Python framework for building APIs quickly |
| **Next.js** | A framework for building React websites |
| **Docker** | A tool that packages software so it runs the same everywhere |
| **Hackathon** | A competition where you build software in a short time |

---

## 13. Change Log

This section tracks every significant change to the project. Updated automatically.

| Date | What Changed | Why | Details |
|---|---|---|---|
| 2026-10-12 | Runnable local prototype and complete revision guide added | Core/API, controlled fixtures, shared dashboard, tests and technical report implemented | See task.md for verification and unresolved real-data/environment work |
| 2026-10-12 | Initial planning documents created | Starting the project | PRD, TDD, implementation strategy, task tracker, and this guide |
| 2026-10-12 | Added file-by-file reading order guide | User asked for a sequential map of every file in the project | Section 0 — complete reading roadmap with 6 parts (A-F), ~30 files |

---

> **Note to future me**: Every time we implement something new, come back here and:
> 1. Update the relevant section with what was actually built
> 2. Add any new technology choices and their rationale
> 3. Update the Change Log
> 4. Add any new terms to the Glossary
