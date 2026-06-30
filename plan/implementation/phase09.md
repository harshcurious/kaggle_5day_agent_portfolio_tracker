# Phase 9 — Critic Guardrail Loop

## Completed plan steps

- Added deterministic Python memo checks before LLM critic invocation.
- Routed deterministic failures back to the CIO agent with specific feedback and failed check IDs.
- Invoked the LLM critic only after deterministic checks pass.
- Added bounded revision handling with a default maximum of 2 revisions.
- Added visible best-effort warning text when guardrails still fail after maximum revisions.

## High-level code changes

- Added `run_critic_guardrail_loop(...)` in `src/portfolio_tracker/workflow.py`.
- Added `deterministic_memo_checks(...)` for required disclaimer text, non-empty `key_risks`, and prohibited speculative language.
- Added revision request and agent-run helpers supporting sync or async agent wrappers.
- Added best-effort memo warning prefix for exhausted guardrail loops.

## Additional implementation decisions

- Deterministic checks return a `CriticResult` so CIO revision feedback uses the same contract as LLM critic feedback.
- Revision count is enforced by workflow code and set to the previous memo revision plus one, rather than trusting model output.
- The LLM critic is skipped for the failed draft itself, then used after a revised memo passes deterministic checks.

## Tests created

- `tests/unit/test_critic_loop.py`
  - Verifies prohibited speculative language is rejected and routed to CIO before critic review.
  - Verifies missing risks are caught deterministically.
  - Verifies deterministic-pass memos invoke the LLM critic.
  - Verifies infinite rewrite loops stop after exactly 2 revisions with a guardrail warning.

## Commit message

`feat: add critic guardrail revision loop`
