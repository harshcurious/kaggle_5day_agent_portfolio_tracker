"""Domain schemas for the Market Signal Synthesizer."""

from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, Field, StrictFloat, field_validator, model_validator


_TICKER_PATTERN = re.compile(r"^[A-Z0-9]+(?:[.-][A-Z0-9]+)?$")
_SECRET_OR_TRACEBACK_PATTERN = re.compile(
    r"(traceback|api[_-]?key|secret|token|password|authorization)", re.IGNORECASE
)


def _normalize_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not ticker:
        raise ValueError("ticker is required")
    if len(ticker) > 5:
        raise ValueError("ticker must be 1 to 5 characters")
    if not _TICKER_PATTERN.fullmatch(ticker):
        raise ValueError("ticker may contain only letters, digits, dots, or hyphens")
    return ticker


def _non_empty(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def _sanitize_failure_text(value: str | None) -> str | None:
    if value is None:
        return None
    if _SECRET_OR_TRACEBACK_PATTERN.search(value):
        return "Data source failed; details withheld."
    return value.strip() or None


class DataSourceStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class TickerRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        return _normalize_ticker(value)


class BaseVectorAnalysis(BaseModel):
    ticker: str
    status: DataSourceStatus
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        return _normalize_ticker(value)

    @field_validator("error_message")
    @classmethod
    def sanitize_error_message(cls, value: str | None) -> str | None:
        return _sanitize_failure_text(value)

    @field_validator("warnings")
    @classmethod
    def sanitize_warnings(cls, value: list[str]) -> list[str]:
        return [sanitized for item in value if (sanitized := _sanitize_failure_text(item))]


class PerformanceAnalysis(BaseVectorAnalysis):
    period_years: int = Field(gt=0)
    cagr_10yr: StrictFloat | None = None
    max_drawdown: StrictFloat | None = None
    dividend_consistency: str | None = None

    @field_validator("cagr_10yr")
    @classmethod
    def validate_cagr(cls, value: float | None) -> float | None:
        if value is not None and value > 10.0:
            raise ValueError("cagr_10yr cannot exceed 1000%")
        return value

    @field_validator("max_drawdown")
    @classmethod
    def validate_max_drawdown(cls, value: float | None) -> float | None:
        if value is not None and value > 0:
            raise ValueError("max_drawdown cannot be positive")
        return value


class FundamentalAnalysis(BaseVectorAnalysis):
    filing_years: list[int]
    revenue_trajectory: str | None = None
    debt_profile: str | None = None
    fundamental_red_flags: list[str] = Field(default_factory=list)


class SentimentAnalysis(BaseVectorAnalysis):
    quarter: str | None = None
    year: int | None = None
    management_confidence: str
    capital_allocation_plans: list[str] = Field(default_factory=list)
    analyst_concerns: list[str] = Field(default_factory=list)

    @field_validator("management_confidence")
    @classmethod
    def validate_management_confidence(cls, value: str) -> str:
        allowed = {"High", "Neutral", "Low", "Unknown"}
        if value not in allowed:
            raise ValueError(f"management_confidence must be one of {sorted(allowed)}")
        return value


class MacroAnalysis(BaseVectorAnalysis):
    regulatory_environment: str | None = None
    macro_headwinds: list[str] = Field(default_factory=list)
    competitive_shifts: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class SynthesizerInput(BaseModel):
    ticker: str
    performance: PerformanceAnalysis
    fundamentals: FundamentalAnalysis
    sentiment: SentimentAnalysis
    macro: MacroAnalysis

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        return _normalize_ticker(value)

    @model_validator(mode="after")
    def validate_matching_tickers(self) -> "SynthesizerInput":
        vector_tickers = {
            self.performance.ticker,
            self.fundamentals.ticker,
            self.sentiment.ticker,
            self.macro.ticker,
        }
        if vector_tickers != {self.ticker}:
            raise ValueError("all vector analyses must match synthesizer ticker")
        return self


class InvestmentMemo(BaseModel):
    ticker: str
    recommendation_summary: str
    long_term_thesis: str
    supporting_evidence: dict[str, Any] = Field(default_factory=dict)
    key_risks: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    not_investment_advice_disclaimer: str
    revision_count: int = Field(ge=0)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        return _normalize_ticker(value)

    @field_validator(
        "recommendation_summary",
        "long_term_thesis",
        "not_investment_advice_disclaimer",
    )
    @classmethod
    def validate_required_text(cls, value: str, info: Any) -> str:
        return _non_empty(value, info.field_name)


class CriticResult(BaseModel):
    passed: bool
    feedback: list[str] = Field(default_factory=list)
    failed_checks: list[str] = Field(default_factory=list)
    grounding_score: float = Field(ge=0, le=1)
