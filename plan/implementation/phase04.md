# Phase 4 — Earnings Call Sentiment Tool

## Completed plan steps

- Implemented `TranscriptAdapter` with API-key support.
- Added `config.py` with `Settings` and `.env` loading for optional API credentials.
- Implemented a `qa_only` preference that extracts the question-and-answer section and filters prepared remarks.
- Implemented transcript bounding to keep transcript context under 10,000 characters by default.
- Ensured authentication and connection exceptions propagate from the adapter for future ADK retry handling.
- Added tests for missing credentials, Q&A extraction, transcript bounding, provider call arguments, analyst concern extraction, and exception propagation.

## Codebase changes

- Added `src/portfolio_tracker/config.py`.
- Added `src/portfolio_tracker/tools/transcript_tools.py`.
- Added `tests/unit/test_transcript_tools.py`.
- Updated the revised implementation plan checkboxes for completed Phase 4 items.

## Tests created

- `tests/unit/test_transcript_tools.py`
  - `test_missing_api_key_skips_sentiment_with_explicit_warning`
  - `test_transcript_qa_fixture_extracts_analyst_concerns`
  - `test_extract_qa_pairs_filters_prepared_remarks_when_qa_only`
  - `test_bound_transcript_text_keeps_context_under_limit`
  - `test_adapter_passes_qa_only_preference_to_provider`
  - `test_adapter_does_not_mask_auth_or_connection_exceptions`

## Additional decisions

- Missing EarningsCall credentials are treated as `DataSourceStatus.SKIPPED`, not `FAILED`, because the data source is optional for local/demo execution.
- The default transcript provider is isolated behind `TranscriptAdapter`; tests inject a provider callable and never make live HTTP requests.
- Sentiment extraction is deterministic for this phase: analyst concerns are pulled from question keywords, capital allocation plans from related Q&A text, and management confidence from simple answer markers.
- The live provider URL is kept as a narrow adapter boundary and can be replaced once a specific EarningsCall vendor contract is finalized.

## Commit message

`feat: add earnings transcript sentiment tool`
