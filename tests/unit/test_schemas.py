import pytest
from pydantic import ValidationError

from portfolio_tracker.schemas import (
    BaseVectorAnalysis,
    CriticResult,
    DataSourceStatus,
    FundamentalAnalysis,
    InvestmentMemo,
    MacroAnalysis,
    PerformanceAnalysis,
    SentimentAnalysis,
    SynthesizerInput,
    TickerRequest,
)


def valid_performance(ticker: str = "AAPL") -> PerformanceAnalysis:
    return PerformanceAnalysis(
        ticker=ticker,
        status=DataSourceStatus.SUCCESS,
        period_years=10,
        cagr_10yr=0.15,
        max_drawdown=-0.35,
    )


def valid_fundamental(ticker: str = "AAPL") -> FundamentalAnalysis:
    return FundamentalAnalysis(
        ticker=ticker,
        status=DataSourceStatus.SUCCESS,
        filing_years=[2021, 2022, 2023],
    )


def valid_sentiment(ticker: str = "AAPL") -> SentimentAnalysis:
    return SentimentAnalysis(
        ticker=ticker,
        status=DataSourceStatus.SUCCESS,
        management_confidence="Neutral",
    )


def valid_macro(ticker: str = "AAPL") -> MacroAnalysis:
    return MacroAnalysis(
        ticker=ticker,
        status=DataSourceStatus.SUCCESS,
    )


def test_ticker_request_normalizes_to_uppercase() -> None:
    request = TickerRequest(ticker=" msft ")

    assert request.ticker == "MSFT"


@pytest.mark.parametrize("ticker", ["BRK.B", "RDS-A", "AAPL1", "T"])
def test_ticker_request_accepts_common_uppercase_ticker_shapes(ticker: str) -> None:
    assert TickerRequest(ticker=ticker).ticker == ticker


@pytest.mark.parametrize("ticker", ["", "TOOLONG", "AA$L", "BRK/B", "MS FT"])
def test_ticker_request_rejects_invalid_tickers(ticker: str) -> None:
    with pytest.raises(ValidationError):
        TickerRequest(ticker=ticker)


def test_data_source_status_values_are_stable_strings() -> None:
    assert [status.value for status in DataSourceStatus] == [
        "success",
        "partial",
        "failed",
        "skipped",
    ]


def test_base_vector_analysis_defaults_and_serializes_status() -> None:
    payload = BaseVectorAnalysis(ticker="aapl", status=DataSourceStatus.FAILED)

    assert payload.ticker == "AAPL"
    assert payload.warnings == []
    assert payload.model_dump(mode="json") == {
        "ticker": "AAPL",
        "status": "failed",
        "warnings": [],
        "error_message": None,
    }


def test_failed_status_error_message_is_sanitized_for_secrets_and_tracebacks() -> None:
    payload = BaseVectorAnalysis(
        ticker="AAPL",
        status=DataSourceStatus.FAILED,
        error_message="Traceback (most recent call last):\nAPI_KEY=secret-token failed",
    )

    dumped = payload.model_dump(mode="json")

    assert "Traceback" not in dumped["error_message"]
    assert "secret-token" not in dumped["error_message"]
    assert "API_KEY" not in dumped["error_message"]


def test_failed_status_warnings_are_sanitized_for_secrets_and_tracebacks() -> None:
    payload = BaseVectorAnalysis(
        ticker="AAPL",
        status=DataSourceStatus.FAILED,
        warnings=["Traceback: token=secret-token", "provider timed out"],
    )

    dumped = payload.model_dump(mode="json")

    assert dumped["warnings"] == [
        "Data source failed; details withheld.",
        "provider timed out",
    ]


def test_performance_analysis_rejects_impossible_metrics() -> None:
    with pytest.raises(ValidationError):
        PerformanceAnalysis(
            ticker="AAPL",
            status=DataSourceStatus.SUCCESS,
            period_years=10,
            cagr_10yr=10.01,
            max_drawdown=-0.2,
        )


def test_performance_analysis_rejects_string_numeric_metrics() -> None:
    with pytest.raises(ValidationError):
        PerformanceAnalysis(
            ticker="AAPL",
            status=DataSourceStatus.SUCCESS,
            period_years=10,
            cagr_10yr="0.1",
            max_drawdown=-0.2,
        )

    with pytest.raises(ValidationError):
        PerformanceAnalysis(
            ticker="AAPL",
            status=DataSourceStatus.SUCCESS,
            period_years=10,
            cagr_10yr=0.1,
            max_drawdown=0.01,
        )


def test_vector_specific_schemas_have_expected_defaults() -> None:
    assert valid_fundamental().fundamental_red_flags == []
    assert valid_sentiment().capital_allocation_plans == []
    assert valid_sentiment().analyst_concerns == []
    assert valid_macro().macro_headwinds == []
    assert valid_macro().competitive_shifts == []
    assert valid_macro().source_urls == []


def test_synthesizer_input_requires_all_four_vectors() -> None:
    with pytest.raises(ValidationError):
        SynthesizerInput(
            ticker="AAPL",
            performance=valid_performance(),
            fundamentals=valid_fundamental(),
            sentiment=valid_sentiment(),
        )


def test_synthesizer_input_requires_same_ticker_for_all_vectors() -> None:
    with pytest.raises(ValidationError):
        SynthesizerInput(
            ticker="AAPL",
            performance=valid_performance("AAPL"),
            fundamentals=valid_fundamental("MSFT"),
            sentiment=valid_sentiment("AAPL"),
            macro=valid_macro("AAPL"),
        )


def test_synthesizer_input_accepts_complete_matching_vectors() -> None:
    payload = SynthesizerInput(
        ticker="aapl",
        performance=valid_performance(),
        fundamentals=valid_fundamental(),
        sentiment=valid_sentiment(),
        macro=valid_macro(),
    )

    assert payload.ticker == "AAPL"


def test_investment_memo_validates_basic_fields() -> None:
    memo = InvestmentMemo(
        ticker="aapl",
        recommendation_summary="Long-term compounder with valuation risk.",
        long_term_thesis="Durable cash generation supports continued reinvestment.",
        not_investment_advice_disclaimer="This is not investment advice.",
        revision_count=0,
    )

    assert memo.ticker == "AAPL"
    assert memo.supporting_evidence == {}
    assert memo.key_risks == []

    with pytest.raises(ValidationError):
        InvestmentMemo(
            ticker="AAPL",
            recommendation_summary="",
            long_term_thesis="Valid thesis",
            not_investment_advice_disclaimer="This is not investment advice.",
            revision_count=-1,
        )


def test_critic_result_validates_basic_fields() -> None:
    result = CriticResult(passed=False, grounding_score=0.5)

    assert result.feedback == []
    assert result.failed_checks == []

    with pytest.raises(ValidationError):
        CriticResult(passed=True, grounding_score=1.1)
