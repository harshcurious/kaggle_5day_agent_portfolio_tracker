import asyncio

import pytest

from portfolio_tracker.schemas import (
    DataSourceStatus,
    FundamentalAnalysis,
    MacroAnalysis,
    PerformanceAnalysis,
    SentimentAnalysis,
    SynthesizerInput,
)
from portfolio_tracker.workflow import (
    Event,
    NodeInterruptedError,
    aggregate_outputs,
    build_workflow,
    failsafe_vector_node,
    is_framework_interruption,
)


def successful_vectors(ticker: str = "MSFT") -> dict[str, Event]:
    return {
        "performance": Event(
            output=PerformanceAnalysis(
                ticker=ticker,
                status=DataSourceStatus.SUCCESS,
                warnings=[],
                period_years=10,
                cagr_10yr=0.1,
                max_drawdown=-0.2,
            )
        ),
        "fundamentals": Event(
            output=FundamentalAnalysis(
                ticker=ticker,
                status=DataSourceStatus.SUCCESS,
                warnings=[],
                filing_years=[2021, 2022, 2023],
            )
        ),
        "sentiment": Event(
            output=SentimentAnalysis(
                ticker=ticker,
                status=DataSourceStatus.SUCCESS,
                warnings=[],
                management_confidence="High",
            )
        ),
        "macro": Event(
            output=MacroAnalysis(
                ticker=ticker,
                status=DataSourceStatus.SUCCESS,
                warnings=[],
                macro_headwinds=["Regulatory scrutiny"],
            )
        ),
    }


def test_aggregate_outputs_compiles_four_vectors_into_synthesizer_input() -> None:
    result = aggregate_outputs(successful_vectors())

    assert isinstance(result.output, SynthesizerInput)
    assert result.output.ticker == "MSFT"
    assert result.output.performance.cagr_10yr == 0.1
    assert result.output.fundamentals.filing_years == [2021, 2022, 2023]
    assert result.output.sentiment.management_confidence == "High"
    assert result.output.macro.macro_headwinds == ["Regulatory scrutiny"]


def test_workflow_completes_when_one_vector_raises_after_retries() -> None:
    async def performance(_: dict[str, str]) -> PerformanceAnalysis:
        return successful_vectors()["performance"].output

    async def fundamentals(_: dict[str, str]) -> FundamentalAnalysis:
        return successful_vectors()["fundamentals"].output

    async def sentiment(_: dict[str, str]) -> SentimentAnalysis:
        raise RuntimeError("provider exhausted retries")

    async def macro(_: dict[str, str]) -> MacroAnalysis:
        return successful_vectors()["macro"].output

    workflow = build_workflow(
        performance_node=performance,
        fundamental_node=fundamentals,
        sentiment_node=sentiment,
        macro_node=macro,
    )

    result = asyncio.run(workflow.run("msft"))

    assert result.ticker == "MSFT"
    assert result.sentiment.status is DataSourceStatus.FAILED
    assert result.sentiment.management_confidence == "Unknown"
    assert result.sentiment.warnings == ["Sentiment agent failed: provider exhausted retries"]
    assert result.performance.status is DataSourceStatus.SUCCESS


def test_failsafe_wrapper_re_raises_framework_interruptions_and_cancellations() -> None:
    async def interrupted(_: dict[str, str]) -> SentimentAnalysis:
        raise NodeInterruptedError("human review requested")

    async def cancelled(_: dict[str, str]) -> SentimentAnalysis:
        raise asyncio.CancelledError()

    with pytest.raises(NodeInterruptedError):
        asyncio.run(
            failsafe_vector_node(
                name="Sentiment",
                ticker="MSFT",
                node=interrupted,
                fallback_factory=SentimentAnalysis,
                fallback_defaults={"management_confidence": "Unknown"},
            )
        )

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            failsafe_vector_node(
                name="Sentiment",
                ticker="MSFT",
                node=cancelled,
                fallback_factory=SentimentAnalysis,
                fallback_defaults={"management_confidence": "Unknown"},
            )
        )

    assert is_framework_interruption(NodeInterruptedError("pause")) is True
