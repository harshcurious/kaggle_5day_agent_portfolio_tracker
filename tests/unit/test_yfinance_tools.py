from __future__ import annotations

import pandas as pd
import pytest

from portfolio_tracker.schemas import DataSourceStatus
from portfolio_tracker.tools.yfinance_tools import (
    YFinanceAdapter,
    analyze_performance,
    calculate_cagr,
    calculate_max_drawdown,
)


def test_calculate_cagr_from_adjusted_close_series() -> None:
    prices = pd.Series(
        [100.0, 200.0],
        index=pd.to_datetime(["2014-01-02", "2024-01-02"]),
        name="Adj Close",
    )

    assert calculate_cagr(prices, years=10) == pytest.approx(0.071773, rel=1e-5)


def test_calculate_max_drawdown_from_price_drop_series() -> None:
    prices = pd.Series([100.0, 120.0, 60.0, 90.0], name="Adj Close")

    assert calculate_max_drawdown(prices) == pytest.approx(-0.5)


def test_analyze_performance_uses_adapter_history_and_dividends() -> None:
    history = pd.DataFrame(
        {
            "Adj Close": [100.0, 200.0],
            "Close": [101.0, 201.0],
        },
        index=pd.to_datetime(["2014-01-02", "2024-01-02"]),
    )
    dividends = pd.Series([0.10, 0.12], index=pd.to_datetime(["2023-01-01", "2024-01-01"]))
    adapter = YFinanceAdapter(ticker_factory=lambda ticker: FakeTicker(history, dividends))

    result = analyze_performance("msft", adapter=adapter)

    assert result.ticker == "MSFT"
    assert result.status is DataSourceStatus.SUCCESS
    assert result.period_years == 10
    assert result.cagr_10yr == pytest.approx(0.071773, rel=1e-5)
    assert result.max_drawdown == pytest.approx(0.0)
    assert result.dividend_consistency == "Dividends recorded"
    assert result.warnings == []


def test_analyze_performance_defaults_safely_when_dividends_missing() -> None:
    history = pd.DataFrame(
        {"Adj Close": [100.0, 110.0]},
        index=pd.to_datetime(["2014-01-02", "2024-01-02"]),
    )
    adapter = YFinanceAdapter(ticker_factory=lambda ticker: FakeTicker(history, pd.Series(dtype=float)))

    result = analyze_performance("AAPL", adapter=adapter)

    assert result.status is DataSourceStatus.SUCCESS
    assert result.dividend_consistency == "No dividends recorded"


def test_analyze_performance_returns_partial_warning_for_empty_history() -> None:
    adapter = YFinanceAdapter(
        ticker_factory=lambda ticker: FakeTicker(pd.DataFrame(), pd.Series(dtype=float))
    )

    result = analyze_performance("AAPL", adapter=adapter)

    assert result.status is DataSourceStatus.PARTIAL
    assert result.cagr_10yr is None
    assert result.max_drawdown is None
    assert "No price history returned" in result.warnings


def test_analyze_performance_returns_partial_warning_for_truncated_history() -> None:
    history = pd.DataFrame(
        {"Adj Close": [100.0, 110.0]},
        index=pd.to_datetime(["2023-01-02", "2024-01-02"]),
    )
    adapter = YFinanceAdapter(ticker_factory=lambda ticker: FakeTicker(history, pd.Series(dtype=float)))

    result = analyze_performance("AAPL", adapter=adapter)

    assert result.status is DataSourceStatus.PARTIAL
    assert any("less than 10 years" in warning for warning in result.warnings)


def test_adapter_does_not_mask_yfinance_exceptions() -> None:
    adapter = YFinanceAdapter(ticker_factory=lambda ticker: ExplodingTicker())

    with pytest.raises(TimeoutError):
        adapter.get_history("AAPL")


class FakeTicker:
    def __init__(self, history: pd.DataFrame, dividends: pd.Series) -> None:
        self._history = history
        self.dividends = dividends
        self.history_calls: list[dict[str, object]] = []

    def history(self, **kwargs: object) -> pd.DataFrame:
        self.history_calls.append(kwargs)
        return self._history


class ExplodingTicker:
    @property
    def dividends(self) -> pd.Series:
        return pd.Series(dtype=float)

    def history(self, **kwargs: object) -> pd.DataFrame:
        raise TimeoutError("temporary yfinance timeout")
