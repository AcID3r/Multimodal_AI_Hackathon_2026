"""FastAPI entry point. Uploads stay in memory; result cache is bounded and ephemeral."""
from collections import OrderedDict
import importlib.util
import json
import logging
import threading
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from backend.config import ALGORITHM_VERSION, MAX_UPLOAD_BYTES, RESULT_LIMIT, ROOT
from backend.core.dataset import get_baseline, list_baselines
from backend.core.pipeline import analyze
from backend.models.schemas import Alignment, AnalysisResult

app = FastAPI(title="Cadence: Contrastive Speech Analytics", version=ALGORITHM_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
results: OrderedDict[str, AnalysisResult] = OrderedDict()
results_lock = threading.Lock()
processing_lock = threading.Lock()


def remember(result: AnalysisResult):
    with results_lock:
        results[result.analysis_id] = result
        results.move_to_end(result.analysis_id)
        while len(results) > RESULT_LIMIT:
            results.popitem(last=False)


async def read_limited(upload: UploadFile, limit: int) -> bytes:
    try:
        chunks, total = [], 0
        while chunk := await upload.read(min(1024 * 1024, limit + 1)):
            total += len(chunk)
            if total > limit:
                raise ValueError("Uploaded file exceeds its size limit")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        await upload.close()


def execute(*args, **kwargs):
    # Keep CPU memory bounded rather than running many 10-minute jobs concurrently.
    if not processing_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="An analysis is already running; please try again shortly")
    try:
        result = analyze(*args, **kwargs)
        remember(result)
        return result
    finally:
        processing_lock.release()


@app.get("/api/health")
def health():
    return {"status": "ok", "algorithm_version": ALGORITHM_VERSION,
            "whisperx_available": importlib.util.find_spec("whisperx") is not None, "baseline_count": len(list_baselines())}


@app.get("/api/baselines")
def baselines():
    return [{**entry, "transcript": get_baseline(entry["id"])[2]} for entry in list_baselines()]


@app.get("/api/baselines/{baseline_id}/audio")
def baseline_audio(baseline_id: str, variant: str = "ideal"):
    if variant not in ("ideal", "flawed_level_1", "flawed_level_2", "flawed_level_3"):
        raise HTTPException(400, "Unknown variant")
    try:
        _, folder, _, _ = get_baseline(baseline_id)
        return FileResponse(folder / variant / "audio.wav", media_type="audio/wav")
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/analyze", response_model=AnalysisResult)
@app.post("/api/baselines/compare", response_model=AnalysisResult)
async def analyze_upload(audio: UploadFile = File(...), baseline_id: str = Form(...),
                         transcript_text: str = Form(""), transcript: UploadFile | None = File(None),
                         alignment: UploadFile | None = File(None), alignment_mode: str = Form("forced"),
                         threshold: float = Form(1.5)):
    try:
        if alignment_mode not in ("forced", "estimated") or not 0.5 <= threshold <= 5:
            raise ValueError("Invalid alignment mode or sensitivity (0.5-5)")
        if not audio.filename or audio.filename.lower().rsplit(".", 1)[-1] not in ("wav", "mp3", "flac"):
            raise ValueError("Upload a WAV, MP3 or FLAC file")
        entry, folder, text, b_align = get_baseline(baseline_id)
        supplied_text = (await read_limited(transcript, 100_000)).decode("utf-8-sig") if transcript else transcript_text
        if supplied_text.strip():
            from backend.core.alignment import tokens
            if tokens(supplied_text) != tokens(text):
                raise ValueError("Participant transcript must match the selected baseline text")
        p_align = Alignment.model_validate_json(await read_limited(alignment, 2_000_000)) if alignment else None
        raw = await read_limited(audio, MAX_UPLOAD_BYTES)
        return await run_in_threadpool(execute, raw, baseline_id, folder / "ideal" / "audio.wav", text, b_align, p_align, alignment_mode, threshold)
    except (ValueError, ValidationError, UnicodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Analysis failed")
        raise HTTPException(503, "Analysis failed. Check backend logs and optional model setup.") from exc


@app.post("/api/demo/{baseline_id}/{level}", response_model=AnalysisResult)
def demo(baseline_id: str, level: int):
    try:
        if level not in (0, 1, 2, 3):
            raise ValueError("Level must be 0 (baseline), 1, 2 or 3")
        _, folder, text, b_align = get_baseline(baseline_id)
        variant = folder / (f"flawed_level_{level}" if level else "ideal")
        p_align = Alignment.model_validate_json((variant / "alignment.json").read_text(encoding="utf-8"))
        return execute((variant / "audio.wav").read_bytes(), baseline_id, folder / "ideal" / "audio.wav", text, b_align, p_align)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/analyze/{analysis_id}", response_model=AnalysisResult)
def get_result(analysis_id: str):
    with results_lock:
        result = results.get(analysis_id)
    if result is None:
        raise HTTPException(404, "Result expired or does not exist; run analysis again")
    return result

# A dependency-free dashboard is available even when npm installation is blocked.
app.mount("/assets", StaticFiles(directory=ROOT / "frontend" / "public"), name="assets")


@app.get("/", include_in_schema=False)
def local_dashboard():
    return FileResponse(ROOT / "frontend" / "public" / "local.html")
