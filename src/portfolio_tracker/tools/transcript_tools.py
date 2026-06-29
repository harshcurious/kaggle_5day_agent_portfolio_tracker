"""Earnings-call transcript sentiment tools."""

from __future__ import annotations

import re
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from portfolio_tracker.config import Settings, load_settings
from portfolio_tracker.schemas import DataSourceStatus, SentimentAnalysis, TickerRequest


MAX_TRANSCRIPT_CHARS = 10_000


class _TranscriptProvider(Protocol):
    def __call__(self, **kwargs: object) -> str: ...


class TranscriptAdapter:
    """Thin transcript adapter that lets auth/network exceptions propagate."""

    def __init__(
        self,
        *,
        api_key: str,
        transcript_provider: _TranscriptProvider | None = None,
    ) -> None:
        self.api_key = api_key
        self._transcript_provider = transcript_provider or _default_transcript_provider

    def fetch_latest_transcript(self, ticker: str, *, qa_only: bool = True) -> str:
        normalized_ticker = TickerRequest(ticker=ticker).ticker
        return self._transcript_provider(
            ticker=normalized_ticker,
            api_key=self.api_key,
            qa_only=qa_only,
        )


def analyze_transcript_sentiment(
    ticker: str,
    *,
    settings: Settings | None = None,
    adapter: TranscriptAdapter | None = None,
    qa_only: bool = True,
    max_chars: int = MAX_TRANSCRIPT_CHARS,
) -> SentimentAnalysis:
    """Build a deterministic sentiment analysis from latest earnings-call Q&A."""

    normalized_ticker = TickerRequest(ticker=ticker).ticker
    settings = settings or load_settings()

    if not settings.earningscall_api_key:
        return SentimentAnalysis(
            ticker=normalized_ticker,
            status=DataSourceStatus.SKIPPED,
            warnings=["EarningsCall API credentials missing"],
            management_confidence="Unknown",
        )

    adapter = adapter or TranscriptAdapter(api_key=settings.earningscall_api_key)
    transcript = adapter.fetch_latest_transcript(normalized_ticker, qa_only=qa_only)
    bounded_transcript = bound_transcript_text(transcript, max_chars=max_chars)
    qa_pairs = extract_qa_pairs(bounded_transcript, qa_only=qa_only)

    return SentimentAnalysis(
        ticker=normalized_ticker,
        status=DataSourceStatus.SUCCESS,
        management_confidence=_management_confidence(qa_pairs),
        capital_allocation_plans=_capital_allocation_plans(qa_pairs),
        analyst_concerns=_analyst_concerns(qa_pairs),
    )


def bound_transcript_text(transcript: str, *, max_chars: int = MAX_TRANSCRIPT_CHARS) -> str:
    return _normalize_whitespace(transcript)[:max_chars]


def extract_qa_pairs(transcript: str, *, qa_only: bool = True) -> list[tuple[str, str]]:
    text = _qa_section(transcript) if qa_only else transcript
    speaker_turns = _speaker_turns(text)
    pairs: list[tuple[str, str]] = []
    current_question: str | None = None

    for speaker, content in speaker_turns:
        speaker_lower = speaker.lower()
        if "analyst" in speaker_lower:
            current_question = content
        elif "management" in speaker_lower and current_question:
            pairs.append((current_question, content))
            current_question = None

    return pairs


def _default_transcript_provider(*, ticker: str, api_key: str, qa_only: bool) -> str:
    query = urlencode({"ticker": ticker, "qa_only": str(qa_only).lower()})
    request = Request(
        f"https://api.earningscall.biz/v1/transcripts/latest?{query}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - explicit adapter boundary.
        return response.read().decode("utf-8")


def _qa_section(transcript: str) -> str:
    start_match = re.search(
        r"question-and-answer portion|q&a session|\bq&a\b",
        transcript,
        flags=re.IGNORECASE,
    )
    start = start_match.start() if start_match else 0
    end_match = re.search(
        r"this concludes (today's )?q&a session|this concludes",
        transcript[start:],
        flags=re.IGNORECASE,
    )
    end = start + end_match.end() if end_match else len(transcript)
    return transcript[start:end]


def _speaker_turns(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"(?P<speaker>Analyst|Management|Operator)\s*:\s*(?P<content>.*?)(?=\n\s*(?:Analyst|Management|Operator)\s*:|$)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    return [
        (match.group("speaker"), _normalize_whitespace(match.group("content")))
        for match in pattern.finditer(text)
        if _normalize_whitespace(match.group("content"))
    ]


def _analyst_concerns(qa_pairs: list[tuple[str, str]]) -> list[str]:
    concern_keywords = [
        "delay",
        "delaying",
        "uncertainty",
        "pressure",
        "risk",
        "concern",
        "decline",
        "weakness",
        "slowdown",
    ]
    return [
        question.rstrip("?")
        for question, _answer in qa_pairs
        if any(keyword in question.lower() for keyword in concern_keywords)
    ]


def _capital_allocation_plans(qa_pairs: list[tuple[str, str]]) -> list[str]:
    keywords = ["capital allocation", "buyback", "dividend", "shareholder returns", "investment"]
    plans: list[str] = []
    for question, answer in qa_pairs:
        combined = f"{question} {answer}"
        if any(keyword in combined.lower() for keyword in keywords):
            plans.append(combined.rstrip("?"))
    return plans


def _management_confidence(qa_pairs: list[tuple[str, str]]) -> str:
    answers = " ".join(answer for _question, answer in qa_pairs).lower()
    if not answers:
        return "Unknown"
    low_markers = ["challenging", "pressure", "decline", "weakness"]
    high_markers = ["confident", "strong demand", "accelerating", "robust"]
    cautious_markers = ["monitoring", "some", "carefully", "uncertainty", "elevated"]
    if any(marker in answers for marker in low_markers):
        return "Low"
    if any(marker in answers for marker in high_markers) and not any(
        marker in answers for marker in cautious_markers
    ):
        return "High"
    return "Neutral"


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()
