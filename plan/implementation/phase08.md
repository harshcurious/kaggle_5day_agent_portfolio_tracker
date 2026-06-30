# Phase 8 — CIO Synthesis Node

## Completed plan steps

- Passed aggregated `SynthesizerInput` payloads into the CIO agent prompt context.
- Directed CIO synthesis output through `InvestmentMemo` Pydantic validation.
- Added deterministic enforcement so failed or partial vector statuses are disclosed in final memo `data_gaps`.

## High-level code changes

- Added `cio_synthesis_node(...)` to `src/portfolio_tracker/workflow.py`.
- The node serializes `SynthesizerInput` with `model_dump(mode="json")` before calling the CIO agent.
- The node validates CIO output as `InvestmentMemo` and returns it in an `Event` envelope.
- Added data-gap merge helpers to preserve LLM-provided gaps while appending required source-status gaps.

## Additional implementation decisions

- Data-gap enforcement is deterministic after LLM generation, so the final memo cannot omit known failed or partial data vectors.
- Existing model-provided data gaps are preserved and de-duplicated before required gaps are appended.
- Both synchronous and awaitable CIO agent results are supported for compatibility with current fake clients and future async wrappers.

## Tests created

- `tests/unit/test_cio_synthesis.py`
  - Verifies CIO synthesis returns a schema-valid `InvestmentMemo`.
  - Verifies the CIO receives the aggregated `SynthesizerInput` context.
  - Verifies failed and partial vectors are explicitly added to memo `data_gaps`.

## Commit message

`feat: add CIO synthesis workflow node`
