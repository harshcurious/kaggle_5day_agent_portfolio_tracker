"""Workflow orchestration for vector fan-out and deterministic join aggregation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeVar

from portfolio_tracker.schemas import (
    BaseVectorAnalysis,
    DataSourceStatus,
    FundamentalAnalysis,
    InvestmentMemo,
    MacroAnalysis,
    PerformanceAnalysis,
    SentimentAnalysis,
    SynthesizerInput,
    TickerRequest,
)


VectorT = TypeVar("VectorT", bound=BaseVectorAnalysis)
VectorNode = Callable[[dict[str, str]], Awaitable[VectorT] | VectorT]
CioAgent = Any


class NodeInterruptedError(Exception):
    """Local stand-in for ADK interruption/HITL errors in offline tests."""


@dataclass(frozen=True)
class Event:
    """Small event envelope matching the ADK-style output handoff."""

    output: Any


@dataclass(frozen=True)
class JoinNode:
    """Collector marker for the vector fan-out join point."""

    name: str = "collector"


@dataclass(frozen=True)
class Workflow:
    """Executable local workflow for the Phase 7 fan-out/join segment."""

    performance_node: VectorNode[PerformanceAnalysis]
    fundamental_node: VectorNode[FundamentalAnalysis]
    sentiment_node: VectorNode[SentimentAnalysis]
    macro_node: VectorNode[MacroAnalysis]
    collector: JoinNode
    edges: tuple[tuple[str, ...], ...]

    async def run(self, ticker: str) -> SynthesizerInput:
        request = TickerRequest(ticker=ticker)
        payload = {"ticker": request.ticker}

        performance, fundamentals, sentiment, macro = await asyncio.gather(
            failsafe_vector_node(
                name="Performance",
                ticker=request.ticker,
                node=self.performance_node,
                fallback_factory=PerformanceAnalysis,
                fallback_defaults={"period_years": 10},
            ),
            failsafe_vector_node(
                name="Fundamental",
                ticker=request.ticker,
                node=self.fundamental_node,
                fallback_factory=FundamentalAnalysis,
                fallback_defaults={"filing_years": []},
            ),
            failsafe_vector_node(
                name="Sentiment",
                ticker=request.ticker,
                node=self.sentiment_node,
                fallback_factory=SentimentAnalysis,
                fallback_defaults={"management_confidence": "Unknown"},
            ),
            failsafe_vector_node(
                name="Macro",
                ticker=request.ticker,
                node=self.macro_node,
                fallback_factory=MacroAnalysis,
                fallback_defaults={},
            ),
        )

        return aggregate_outputs(
            {
                "performance": performance,
                "fundamentals": fundamentals,
                "sentiment": sentiment,
                "macro": macro,
            },
            node_input=payload,
        ).output


def is_framework_interruption(exc: Exception) -> bool:
    """Return True for ADK/framework control-flow exceptions."""

    return exc.__class__.__name__ in {"NodeInterruptedError"}


async def failsafe_vector_node(
    *,
    name: str,
    ticker: str,
    node: VectorNode[VectorT],
    fallback_factory: type[VectorT],
    fallback_defaults: Mapping[str, Any],
) -> Event:
    """Run a vector node and convert terminal provider failures to events."""

    try:
        result = node({"ticker": ticker})
        if isinstance(result, Awaitable):
            result = await result
        return Event(output=result)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        if is_framework_interruption(exc):
            raise
        return Event(
            output=fallback_factory(
                ticker=ticker,
                status=DataSourceStatus.FAILED,
                warnings=[f"{name} agent failed: {exc}"],
                **dict(fallback_defaults),
            )
        )


def aggregate_outputs(
    collected_events: Mapping[str, Event | BaseVectorAnalysis],
    *,
    node_input: Mapping[str, str] | None = None,
) -> Event:
    """Build a SynthesizerInput from joined vector events."""

    vectors = {key: _event_output(value) for key, value in collected_events.items()}
    ticker = (node_input or {}).get("ticker") or _first_vector_ticker(vectors)
    return Event(
        output=SynthesizerInput(
            ticker=ticker,
            performance=PerformanceAnalysis.model_validate(vectors["performance"]),
            fundamentals=FundamentalAnalysis.model_validate(vectors["fundamentals"]),
            sentiment=SentimentAnalysis.model_validate(vectors["sentiment"]),
            macro=MacroAnalysis.model_validate(vectors["macro"]),
        )
    )


def build_workflow(
    *,
    performance_node: VectorNode[PerformanceAnalysis],
    fundamental_node: VectorNode[FundamentalAnalysis],
    sentiment_node: VectorNode[SentimentAnalysis],
    macro_node: VectorNode[MacroAnalysis],
) -> Workflow:
    """Assemble the Phase 7 fan-out/join workflow graph."""

    collector = JoinNode(name="collector")
    return Workflow(
        performance_node=performance_node,
        fundamental_node=fundamental_node,
        sentiment_node=sentiment_node,
        macro_node=macro_node,
        collector=collector,
        edges=(
            ("START", "validate_request"),
            ("validate_request", "failsafe_performance_node", collector.name),
            ("validate_request", "failsafe_fundamental_node", collector.name),
            ("validate_request", "failsafe_sentiment_node", collector.name),
            ("validate_request", "failsafe_macro_node", collector.name),
            (collector.name, "aggregate_outputs"),
        ),
    )


async def cio_synthesis_node(synthesizer_input: SynthesizerInput, *, agent: CioAgent) -> Event:
    """Run CIO synthesis and enforce deterministic data-gap disclosures."""

    payload = synthesizer_input.model_dump(mode="json")
    result = agent.run(payload)
    if isinstance(result, Awaitable):
        result = await result

    memo = InvestmentMemo.model_validate(result)
    enforced_gaps = _merge_unique(memo.data_gaps, _vector_data_gaps(synthesizer_input))
    return Event(output=memo.model_copy(update={"data_gaps": enforced_gaps}))


def _event_output(value: Event | BaseVectorAnalysis) -> Any:
    if isinstance(value, Event):
        return value.output
    return value


def _first_vector_ticker(vectors: Mapping[str, Any]) -> str:
    for vector in vectors.values():
        if isinstance(vector, BaseVectorAnalysis):
            return vector.ticker
        if isinstance(vector, Mapping) and "ticker" in vector:
            return str(vector["ticker"])
    raise ValueError("cannot infer ticker from collected events")


def _vector_data_gaps(synthesizer_input: SynthesizerInput) -> list[str]:
    return [
        gap
        for label, vector in (
            ("Performance", synthesizer_input.performance),
            ("Fundamental", synthesizer_input.fundamentals),
            ("Sentiment", synthesizer_input.sentiment),
            ("Macro", synthesizer_input.macro),
        )
        if (gap := _data_gap_for_vector(label, vector))
    ]


def _data_gap_for_vector(label: str, vector: BaseVectorAnalysis) -> str | None:
    if vector.status is DataSourceStatus.SUCCESS:
        return None

    reason = vector.error_message or "; ".join(vector.warnings)
    suffix = f": {reason}" if reason else ""
    if vector.status is DataSourceStatus.PARTIAL:
        return f"{label} data partially available{suffix}"
    return f"{label} data unavailable{suffix}"


def _merge_unique(existing: list[str], required: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*existing, *required]:
        if item not in merged:
            merged.append(item)
    return merged
