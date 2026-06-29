"""yfinance-backed performance analysis tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import pandas as pd
import yfinance as yf

from portfolio_tracker.schemas import DataSourceStatus, PerformanceAnalysis, TickerRequest


class _TickerLike(Protocol):
    dividends: pd.Series

    def history(self, **kwargs: object) -> pd.DataFrame: ...


def calculate_cagr(prices: pd.Series, *, years: int) -> float:
    """Calculate compound annual growth rate from first and last prices."""

    clean_prices = _clean_prices(prices)
    if len(clean_prices) < 2:
        raise ValueError("at least two prices are required to calculate CAGR")
    if years <= 0:
        raise ValueError("years must be positive")

    starting_price = float(clean_prices.iloc[0])
    ending_price = float(clean_prices.iloc[-1])
    if starting_price <= 0 or ending_price <= 0:
        raise ValueError("prices must be positive to calculate CAGR")

    return (ending_price / starting_price) ** (1 / years) - 1


def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown as a non-positive decimal."""

    clean_prices = _clean_prices(prices)
    if clean_prices.empty:
        raise ValueError("at least one price is required to calculate max drawdown")

    running_peak = clean_prices.cummax()
    drawdowns = clean_prices / running_peak - 1
    return float(drawdowns.min())


class YFinanceAdapter:
    """Thin yfinance adapter that intentionally lets provider exceptions propagate."""

    def __init__(self, ticker_factory: Callable[[str], _TickerLike] | None = None) -> None:
        self._ticker_factory = ticker_factory or yf.Ticker

    def get_history(self, ticker: str, *, period: str = "10y") -> pd.DataFrame:
        yf_ticker = self._ticker_factory(TickerRequest(ticker=ticker).ticker)
        return yf_ticker.history(period=period, interval="1d", actions=True, raise_errors=True)

    def get_dividends(self, ticker: str) -> pd.Series:
        yf_ticker = self._ticker_factory(TickerRequest(ticker=ticker).ticker)
        return yf_ticker.dividends


def analyze_performance(
    ticker: str,
    *,
    adapter: YFinanceAdapter | None = None,
    period_years: int = 10,
) -> PerformanceAnalysis:
    """Build a structured ten-year performance analysis for a ticker."""

    normalized_ticker = TickerRequest(ticker=ticker).ticker
    adapter = adapter or YFinanceAdapter()

    history = adapter.get_history(normalized_ticker, period=f"{period_years}y")
    warnings: list[str] = []

    if history.empty:
        return PerformanceAnalysis(
            ticker=normalized_ticker,
            status=DataSourceStatus.PARTIAL,
            warnings=["No price history returned"],
            period_years=period_years,
            dividend_consistency="No dividends recorded",
        )

    price_column = _select_price_column(history)
    prices = _clean_prices(history[price_column])
    if len(prices) < 2:
        warnings.append("Insufficient price points returned")

    observed_years = _observed_years(prices)
    if observed_years < period_years * 0.9:
        warnings.append(
            f"Price history covers {observed_years:.1f} years, less than {period_years} years requested"
        )

    dividends = adapter.get_dividends(normalized_ticker)
    dividend_consistency = (
        "No dividends recorded" if dividends is None or dividends.empty else "Dividends recorded"
    )

    return PerformanceAnalysis(
        ticker=normalized_ticker,
        status=DataSourceStatus.PARTIAL if warnings else DataSourceStatus.SUCCESS,
        warnings=warnings,
        period_years=period_years,
        cagr_10yr=calculate_cagr(prices, years=period_years) if len(prices) >= 2 else None,
        max_drawdown=calculate_max_drawdown(prices) if not prices.empty else None,
        dividend_consistency=dividend_consistency,
    )


def _clean_prices(prices: pd.Series) -> pd.Series:
    return prices.dropna().astype(float)


def _select_price_column(history: pd.DataFrame) -> str:
    if "Adj Close" in history.columns:
        return "Adj Close"
    if "Close" in history.columns:
        return "Close"
    raise ValueError("history must include Adj Close or Close price column")


def _observed_years(prices: pd.Series) -> float:
    if len(prices) < 2 or not isinstance(prices.index, pd.DatetimeIndex):
        return 0.0
    observed_days = (prices.index.max() - prices.index.min()).days
    return observed_days / 365.25
