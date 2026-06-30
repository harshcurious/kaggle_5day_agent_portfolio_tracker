import asyncio

from portfolio_tracker.schemas import (
    DataSourceStatus,
    FundamentalAnalysis,
    InvestmentMemo,
    MacroAnalysis,
    PerformanceAnalysis,
    SentimentAnalysis,
    SynthesizerInput,
)
from portfolio_tracker.workflow import cio_synthesis_node


def synthesizer_input_with_failed_sentiment() -> SynthesizerInput:
    return SynthesizerInput(
        ticker="MSFT",
        performance=PerformanceAnalysis(
            ticker="MSFT",
            status=DataSourceStatus.SUCCESS,
            warnings=[],
            period_years=10,
            cagr_10yr=0.11,
            max_drawdown=-0.25,
        ),
        fundamentals=FundamentalAnalysis(
            ticker="MSFT",
            status=DataSourceStatus.PARTIAL,
            warnings=["Only two filings available"],
            filing_years=[2022, 2023],
        ),
        sentiment=SentimentAnalysis(
            ticker="MSFT",
            status=DataSourceStatus.FAILED,
            warnings=["Sentiment agent failed: provider exhausted retries"],
            management_confidence="Unknown",
        ),
        macro=MacroAnalysis(
            ticker="MSFT",
            status=DataSourceStatus.SUCCESS,
            warnings=[],
            macro_headwinds=["Regulatory scrutiny"],
        ),
    )


def test_cio_synthesis_returns_valid_investment_memo_schema() -> None:
    agent = FakeCioAgent(
        InvestmentMemo(
            ticker="MSFT",
            recommendation_summary="Durable compounder with execution and valuation risk.",
            long_term_thesis="Long-term cash generation supports reinvestment, but risk controls matter.",
            supporting_evidence={"performance": ["Positive 10-year CAGR"]},
            key_risks=["Regulatory scrutiny"],
            data_gaps=[],
            not_investment_advice_disclaimer="This is not investment advice.",
            revision_count=0,
        )
    )

    result = asyncio.run(cio_synthesis_node(synthesizer_input_with_failed_sentiment(), agent=agent))

    assert isinstance(result.output, InvestmentMemo)
    assert result.output.ticker == "MSFT"
    assert agent.inputs[0]["ticker"] == "MSFT"
    assert agent.inputs[0]["sentiment"]["status"] == "failed"


def test_cio_synthesis_enforces_failed_and_partial_vector_data_gaps() -> None:
    agent = FakeCioAgent(
        InvestmentMemo(
            ticker="MSFT",
            recommendation_summary="Durable compounder with incomplete source coverage.",
            long_term_thesis="Evidence is constructive but not complete across all vectors.",
            supporting_evidence={},
            key_risks=["Incomplete source coverage"],
            data_gaps=["Macro source detail limited"],
            not_investment_advice_disclaimer="This is not investment advice.",
            revision_count=1,
        )
    )

    result = asyncio.run(cio_synthesis_node(synthesizer_input_with_failed_sentiment(), agent=agent))

    assert result.output.data_gaps == [
        "Macro source detail limited",
        "Fundamental data partially available: Only two filings available",
        "Sentiment data unavailable: Sentiment agent failed: provider exhausted retries",
    ]


class FakeCioAgent:
    def __init__(self, memo: InvestmentMemo) -> None:
        self.memo = memo
        self.inputs: list[dict] = []

    def run(self, input_payload: dict) -> InvestmentMemo:
        self.inputs.append(input_payload)
        return self.memo
