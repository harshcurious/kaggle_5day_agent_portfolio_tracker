# Phase 1 — Domain Schemas

## Completed plan steps

- Defined `TickerRequest` with ticker normalization and validation.
- Defined `DataSourceStatus` enum values: `SUCCESS`, `PARTIAL`, `FAILED`, `SKIPPED`.
- Defined shared `BaseVectorAnalysis` fields for ticker, status, warnings, and error messages.
- Defined vector schemas: `PerformanceAnalysis`, `FundamentalAnalysis`, `SentimentAnalysis`, and `MacroAnalysis`.
- Defined synthesis and review schemas: `SynthesizerInput`, `InvestmentMemo`, and `CriticResult`.
- Added schema tests for invalid tickers, impossible performance metrics, synthesizer input consistency, memo validation, critic validation, and failure payload serialization.

## Codebase changes

- Added `src/portfolio_tracker/schemas.py` containing the Pydantic v2 domain models.
- Added `tests/unit/test_schemas.py` with focused behavior tests for the schema contracts.
- Updated the revised implementation plan checkboxes for completed Phase 1 items.

## Additional decisions

- Ticker input is normalized by stripping whitespace and converting to uppercase.
- Accepted ticker shapes include common dot and hyphen forms such as `BRK.B` and `RDS-A`.
- Performance metrics use strict floats for CAGR and max drawdown so numeric strings are rejected instead of coerced.
- Secret-like or traceback-like text in `error_message` and `warnings` is sanitized before serialization.
- `SynthesizerInput` enforces that all four vector analyses match the requested ticker.
