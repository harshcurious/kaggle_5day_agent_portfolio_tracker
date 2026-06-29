from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_tracker.config import Settings
from portfolio_tracker.schemas import DataSourceStatus
from portfolio_tracker.tools.transcript_tools import (
    TranscriptAdapter,
    analyze_transcript_sentiment,
    bound_transcript_text,
    extract_qa_pairs,
)


FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_missing_api_key_skips_sentiment_with_explicit_warning() -> None:
    result = analyze_transcript_sentiment(
        "MSFT",
        settings=Settings(earningscall_api_key=None),
        adapter=TranscriptAdapter(api_key="unused", transcript_provider=lambda **kwargs: ""),
    )

    assert result.status is DataSourceStatus.SKIPPED
    assert result.management_confidence == "Unknown"
    assert "EarningsCall API credentials missing" in result.warnings


def test_transcript_qa_fixture_extracts_analyst_concerns() -> None:
    transcript = (FIXTURES / "transcript_qa_sample.txt").read_text()
    adapter = TranscriptAdapter(
        api_key="test-key",
        transcript_provider=lambda **kwargs: transcript,
    )

    result = analyze_transcript_sentiment(
        "msft",
        settings=Settings(earningscall_api_key="test-key"),
        adapter=adapter,
    )

    assert result.ticker == "MSFT"
    assert result.status is DataSourceStatus.SUCCESS
    assert result.management_confidence == "Neutral"
    assert "enterprise customers delaying cloud migrations due to macro uncertainty" in " ".join(
        result.analyst_concerns
    )
    assert "AI infrastructure spending and shareholder returns" in " ".join(
        result.capital_allocation_plans
    )


def test_extract_qa_pairs_filters_prepared_remarks_when_qa_only() -> None:
    transcript = """
    Management: Prepared remarks about revenue growth.
    Operator: We will now begin the question-and-answer portion of the call.
    Analyst: Are margins under pressure?
    Management: We are monitoring costs carefully.
    Operator: This concludes today's Q&A session.
    Management: Closing boilerplate.
    """

    pairs = extract_qa_pairs(transcript, qa_only=True)

    assert pairs == [("Are margins under pressure?", "We are monitoring costs carefully.")]


def test_bound_transcript_text_keeps_context_under_limit() -> None:
    bounded = bound_transcript_text("Management: long answer. " * 1_000, max_chars=1_000)

    assert len(bounded) <= 1_000


def test_adapter_passes_qa_only_preference_to_provider() -> None:
    calls: list[dict[str, object]] = []

    def provider(**kwargs: object) -> str:
        calls.append(kwargs)
        return "Operator: Q&A\nAnalyst: Any risks?\nManagement: We are monitoring demand."

    adapter = TranscriptAdapter(api_key="test-key", transcript_provider=provider)

    adapter.fetch_latest_transcript("aapl", qa_only=True)

    assert calls == [{"ticker": "AAPL", "api_key": "test-key", "qa_only": True}]


def test_adapter_does_not_mask_auth_or_connection_exceptions() -> None:
    adapter = TranscriptAdapter(
        api_key="bad-key",
        transcript_provider=lambda **kwargs: (_ for _ in ()).throw(PermissionError("401")),
    )

    with pytest.raises(PermissionError):
        adapter.fetch_latest_transcript("MSFT")
