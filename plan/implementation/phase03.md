# Phase 3 — Fundamental Data Tool

## Completed plan steps

- Implemented `EdgarAdapter` to query recent 10-K filings through EdgarTools.
- Mapped ticker symbols through the EdgarTools company object and exposed the company CIK in adapter results.
- Queried the 3 most recent 10-K filings by default.
- Implemented bounded Item 7 / Item 8 context extraction.
- Kept extracted filing context under the configured character limit.
- Ensured provider exceptions such as temporary SEC blocks propagate instead of being swallowed.
- Added tests for mocked 10-K responses, bounded extraction, missing filings, CIK exposure, 3-filing limiting, and exception propagation.

## Codebase changes

- Added `src/portfolio_tracker/tools/edgar_tools.py`.
- Added `tests/unit/test_edgar_tools.py`.
- Added `edgartools` to project dependencies.
- Updated the revised implementation plan checkboxes for completed Phase 3 items.

## Tests created

- `tests/unit/test_edgar_tools.py`
  - `test_summarize_fundamentals_uses_mocked_10k_fixture`
  - `test_extract_bounded_filing_context_keeps_text_under_limit`
  - `test_summarize_fundamentals_missing_filings_returns_partial_warning`
  - `test_adapter_queries_three_recent_10ks_and_exposes_cik`
  - `test_adapter_does_not_mask_sec_provider_exceptions`

## Additional decisions

- The production adapter imports `edgar.Company` lazily so tests can use fake providers without importing or contacting SEC services.
- Missing filings return `DataSourceStatus.PARTIAL` with a structured warning and empty `filing_years`.
- Filing context extraction prefers Item 7 and Item 8 sections and falls back to bounded full text if those labels are unavailable.
- Fundamental summaries are deterministic and lightweight: revenue/debt fields are extracted from matching sentences, and risk flags are parsed from explicit `Risk factors:` phrases when available.
- No automatic SEC identity setup was added in this phase; identity/config handling remains a later configuration concern.

## Commit message

`feat: add Edgar fundamentals analysis tool`
