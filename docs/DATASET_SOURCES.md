# Candidate real-speech sources

These five candidate pages were researched on 12 October 2026. They are a source shortlist, **not an imported dataset**. Playback quality, excerpt boundaries, transcript agreement, permission/license notes and baseline quality still need review. The environment's download attempt failed at its configured network proxy; no source audio was downloaded.

| Candidate | Source | Review consideration |
|---|---|---|
| John F. Kennedy, Inaugural Address, 20 January 1961 | [Miller Center](https://millercenter.org/the-presidency/presidential-speeches/january-20-1961-inaugural-address) | Select a continuous excerpt with clear speech. The alternate prod-domain page was unavailable during one fetch. |
| John F. Kennedy, Address on the Space Effort, 12 September 1962 | [Miller Center](https://millercenter.org/the-presidency/presidential-speeches/september-12-1962-address-space-effort) | Match an expressive passage and preserve its punctuation/pauses. |
| Ronald Reagan, Brandenburg Gate Address, 12 June 1987 | [Miller Center](https://millercenter.org/the-presidency/presidential-speeches/june-12-1987-address-brandenburg-gate-berlin-wall) | Page attributes the recording to the National Archives; check recording rights and remove crowd-only sections. |
| Franklin D. Roosevelt, First Inaugural Address, 4 March 1933 | [Miller Center](https://millercenter.org/the-presidency/presidential-speeches/march-4-1933-first-inaugural-address) | Historic recording noise is a confounder; compare noise sensitivity separately. |
| Dwight D. Eisenhower, First Inaugural Address, 20 January 1953 | [Miller Center](https://millercenter.org/the-presidency/presidential-speeches/january-20-1953-first-inaugural-address) | The source page says his speech starts at 9:45 after other ceremony material. Do not use the beginning of the recording blindly. |

Use 30-120 second excerpts. Five sources here contain only four distinct speakers; add more speakers for meaningful held-out speaker evaluation. A prominent speaker alone does not certify every excerpt as ideal rhetorical delivery.

Add actual recordings to `dataset/incoming/`, list them in `dataset/sources.json`, and import them with `python -m scripts.build_dataset --manifest dataset/sources.json`. For optional URL downloading, install yt-dlp and ensure ffmpeg is on PATH, add `audio_url`, `start`, and `end`, then run `python -m scripts.download_sources --manifest dataset/sources.json`. Follow source terms and record actual attribution/permissions rather than copying placeholder license text.
