"""Behavior checks across the signal, alignment, scoring, and HTTP boundaries."""
import io
import json
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from backend.config import SAMPLE_RATE
from backend.core.alignment import map_times, validate_alignment
from backend.core.audio import load_audio
from backend.core.dataset import get_baseline, safe_path
from backend.core.detector import detect_flaws
from backend.core.features import extract_features
from backend.core.pipeline import analyze
from backend.core.scorer import score
from backend.main import app
from backend.models.schemas import Alignment, Word


def wav(audio, sr=SAMPLE_RATE):
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format="WAV", subtype="FLOAT")
    return buffer.getvalue()


@pytest.fixture(scope="module")
def sample():
    _, folder, text, alignment = get_baseline("demo_001")
    return folder, text, alignment


def test_identical_audio_has_no_flaws(sample):
    folder, text, alignment = sample
    result = analyze((folder / "ideal/audio.wav").read_bytes(), "demo_001", folder / "ideal/audio.wav", text, alignment, alignment)
    assert result.overall_score == 100
    assert result.flaw_regions == []
    assert all(s == 10 for s in result.rubric_scores.values())


def test_three_runs_are_byte_identical(sample):
    folder, text, baseline = sample
    alignment = Alignment.model_validate_json((folder / "flawed_level_2/alignment.json").read_text())
    raw = (folder / "flawed_level_2/audio.wav").read_bytes()
    output = [analyze(raw, "demo_001", folder / "ideal/audio.wav", text, baseline, alignment).model_dump_json() for _ in range(3)]
    assert output[0] == output[1] == output[2]
    assert 'NaN' not in output[0] and 'Infinity' not in output[0]


def test_scores_follow_injected_severity(sample):
    folder, text, baseline = sample
    results = []
    for level in (1, 2, 3):
        variant = folder / f"flawed_level_{level}"
        alignment = Alignment.model_validate_json((variant / "alignment.json").read_text())
        result = analyze((variant / "audio.wav").read_bytes(), "demo_001", folder / "ideal/audio.wav", text, baseline, alignment)
        assert all(0 <= f.start_time < f.end_time <= result.duration_seconds for f in result.flaw_regions)
        results.append(result.overall_score)
    assert results[0] < results[1] < results[2]


def test_features_have_expected_shape_and_voiced_pitch(sample):
    folder, _, alignment = sample
    features = extract_features(load_audio(str(folder / "ideal/audio.wav")), alignment)
    assert features.mfcc.shape == (13, len(features.times))
    assert len(features.f0) == len(features.energy_rms) == len(features.times)
    assert np.nanmedian(features.f0) == pytest.approx(140, abs=20)
    assert np.isfinite(features.pitch_relative).any()
    assert np.isnan(features.f0).any()
    assert np.isfinite(features.mfcc).all()
    assert np.isfinite(features.speech_rate).all()


def test_speaker_gain_does_not_penalize_volume(sample):
    folder, text, alignment = sample
    audio = load_audio(str(folder / "ideal/audio.wav"))
    result = analyze(wav(audio * 0.3), "demo_001", folder / "ideal/audio.wav", text, alignment, alignment)
    assert not any(f.category == "volume" for f in result.flaw_regions)


def test_noise_has_no_reliable_pitch():
    rng = np.random.default_rng(4)
    audio = rng.normal(0, .05, SAMPLE_RATE).astype(np.float32)
    alignment = Alignment(words=[Word(word="noise", start=0, end=1)])
    features = extract_features(audio, alignment)
    assert np.isfinite(features.f0).mean() < .1


@pytest.mark.parametrize("audio", [np.zeros(SAMPLE_RATE), np.ones(100), np.full(SAMPLE_RATE, np.nan)])
def test_invalid_audio_is_rejected(audio):
    with pytest.raises(ValueError):
        load_audio(wav(audio))


def test_stereo_resampling():
    t = np.arange(8000)/8000
    mono = .2*np.sin(2*np.pi*120*t)
    audio = load_audio(wav(np.column_stack([mono, mono]), 8000))
    assert audio.shape == (16000,)


def test_alignment_mapping_uses_corresponding_words():
    b = Alignment(words=[Word(word="one", start=0, end=1), Word(word="two", start=2, end=3)])
    p = Alignment(words=[Word(word="one", start=0, end=.5), Word(word="two", start=1, end=1.5)])
    assert np.allclose(map_times(np.array([.25,1.25]),b,p),[.5,2.5])
    with pytest.raises(ValueError, match="match"):
        validate_alignment(p,"different words",2)
    with pytest.raises(ValueError, match="exceed"):
        validate_alignment(b,"one two",1)


def test_dataset_path_traversal():
    with pytest.raises(ValueError, match="escapes"):
        safe_path("../../private.txt")


def test_zero_variance_is_safe_and_pitch_flattening_detected():
    alignment = Alignment(words=[Word(word="word", start=i, end=i+.8) for i in range(3)])
    baseline = {"pitch_range":np.array([4.,4.,4.])}
    identical = detect_flaws(baseline,baseline,alignment)
    assert identical == []
    flaws = detect_flaws(baseline,{"pitch_range":np.zeros(3)},alignment)
    assert len(flaws) == 1 and flaws[0].type == "pitch_monotone"
    overall,rubric = score(flaws,3)
    assert 10 <= overall <= 100
    assert 1 <= rubric["vocal_tone"] < 10


def test_full_http_upload_and_cache(sample):
    folder,text,baseline=sample
    client=TestClient(app)
    assert client.get('/').status_code == 200
    assert client.get('/assets/dashboard.js').status_code == 200
    assert len(client.get('/api/baselines').json()) >= 5
    assert client.get('/api/health').json()['status']=='ok'
    dest=folder/'flawed_level_1'
    response=client.post('/api/analyze',data={'baseline_id':'demo_001','transcript_text':text},files={
        'audio':('speech.wav',(dest/'audio.wav').read_bytes(),'audio/wav'),
        'alignment':('alignment.json',(dest/'alignment.json').read_bytes(),'application/json')})
    assert response.status_code == 200, response.text
    result=response.json()
    assert result['flaw_regions']
    assert client.get('/api/analyze/'+result['analysis_id']).json()==result
    assert client.get('/api/analyze/missing').status_code==404


def test_bad_http_inputs(sample):
    folder,_,_=sample
    client=TestClient(app)
    raw=(folder/'ideal/audio.wav').read_bytes()
    for data,filename in [({'baseline_id':'../x'},'speech.wav'),({'baseline_id':'demo_001','transcript_text':'wrong text'},'speech.wav'),({'baseline_id':'demo_001'},'program.exe')]:
        assert client.post('/api/analyze',data=data,files={'audio':(filename,raw)}).status_code==422
    assert client.get('/api/baselines/demo_001/audio?variant=../../private').status_code==400


def test_estimated_alignment_is_disclosed(sample):
    folder,text,alignment=sample
    result=analyze((folder/'ideal/audio.wav').read_bytes(),'demo_001',folder/'ideal/audio.wav',text,alignment,alignment_mode='estimated')
    assert result.alignment.method=='estimated'
    assert any('Approximate timing' in w for w in result.warnings)


def test_demo_builder_preserves_imported_recordings(tmp_path):
    from scripts.build_dataset import build_demo
    (tmp_path / "metadata.json").write_text(json.dumps({"speeches": [{"id": "demo_001", "kind": "real_speech"}]}))
    with pytest.raises(ValueError, match="will not overwrite"):
        build_demo(tmp_path)
    assert not (tmp_path / "speeches").exists()
