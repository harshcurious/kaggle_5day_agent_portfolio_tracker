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

## Tests created

- `tests/unit/test_schemas.py`
  - `test_ticker_request_normalizes_to_uppercase`
  - `test_ticker_request_accepts_common_uppercase_ticker_shapes`
  - `test_ticker_request_rejects_invalid_tickers`
  - `test_data_source_status_values_are_stable_strings`
  - `test_base_vector_analysis_defaults_and_serializes_status`
  - `test_failed_status_error_message_is_sanitized_for_secrets_and_tracebacks`
  - `test_failed_status_warnings_are_sanitized_for_secrets_and_tracebacks`
  - `test_performance_analysis_rejects_impossible_metrics`
  - `test_performance_analysis_rejects_string_numeric_metrics`
  - `test_vector_specific_schemas_have_expected_defaults`
  - `test_synthesizer_input_requires_all_four_vectors`
  - `test_synthesizer_input_requires_same_ticker_for_all_vectors`
  - `test_synthesizer_input_accepts_complete_matching_vectors`
  - `test_investment_memo_validates_basic_fields`
  - `test_critic_result_validates_basic_fields`

## Additional decisions

- Ticker input is normalized by stripping whitespace and converting to uppercase.
- Accepted ticker shapes include common dot and hyphen forms such as `BRK.B` and `RDS-A`.
- Performance metrics use strict floats for CAGR and max drawdown so numeric strings are rejected instead of coerced.
- Secret-like or traceback-like text in `error_message` and `warnings` is sanitized before serialization.
- `SynthesizerInput` enforces that all four vector analyses match the requested ticker.
