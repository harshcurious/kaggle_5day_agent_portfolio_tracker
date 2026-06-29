# Phase 2 — Performance Data Tool

## Completed plan steps

- Implemented quantitative helper functions for CAGR and max drawdown.
- Wrapped yfinance calls behind `YFinanceAdapter`.
- Ensured provider exceptions propagate from the adapter instead of being swallowed, preserving future ADK retry behavior.
- Implemented structured partial results and warnings for empty or truncated price history.
- Added tests for CAGR, max drawdown, mocked yfinance history, missing dividends, empty history, truncated history, and exception propagation.

## Codebase changes

- Added `src/portfolio_tracker/tools/yfinance_tools.py`.
- Added `tests/unit/test_performance_tools.py`.
- Updated the revised implementation plan checkboxes for completed Phase 2 items.

## Additional decisions

- The adapter calls `Ticker.history(period="10y", interval="1d", actions=True, raise_errors=True)` so yfinance/provider errors can surface to the orchestration layer.
- The analysis prefers `Adj Close` when present and falls back to `Close`.
- Empty history returns `DataSourceStatus.PARTIAL` with no CAGR or max drawdown instead of raising.
- History covering less than 90% of the requested period is treated as partial/truncated.
- Missing dividends are represented as `"No dividends recorded"` rather than an error condition.
- Dividend reporting is currently coarse-grained: `"Dividends recorded"` vs `"No dividends recorded"`.

## Commit message

`feat: implement yfinance performance analysis tool`
