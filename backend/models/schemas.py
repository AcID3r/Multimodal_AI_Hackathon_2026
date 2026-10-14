"""Shared contracts. Timestamps always refer to participant audio, in seconds."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Word(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    word: str = Field(min_length=1, max_length=100)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def valid_interval(self):
        if self.end <= self.start:
            raise ValueError("Word end must be later than start")
        return self


class Alignment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: Literal["provided", "whisperx", "estimated", "synthetic"] = "provided"
    words: list[Word] = Field(min_length=1, max_length=20000)


class Delta(BaseModel):
    baseline: float
    participant: float
    z_score: float
    scale: float
    unit: str


class Explanation(BaseModel):
    summary: str
    mathematical_detail: str
    recommendation: str


class Flaw(BaseModel):
    id: str
    type: str
    category: str
    start_time: float
    end_time: float
    severity: float
    severity_label: str
    transcript_segment: str
    causal_explanation: Explanation
    feature_deltas: dict[str, Delta]


class Series(BaseModel):
    timestamps: list[float]
    baseline: list[float | None]
    participant: list[float | None]
    unit: str


class AnalysisResult(BaseModel):
    analysis_id: str
    algorithm_version: str
    status: Literal["complete"] = "complete"
    baseline_id: str
    duration_seconds: float
    overall_score: float
    rubric_scores: dict[str, float]
    alignment: Alignment
    warnings: list[str]
    flaw_regions: list[Flaw]
    feature_timeseries: dict[str, Series]
