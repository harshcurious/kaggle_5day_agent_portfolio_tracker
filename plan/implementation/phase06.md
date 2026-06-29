# Phase 6 — Agent Prompt and Node Wrapper Layer

## Completed plan steps

- Implemented prompt definitions in `src/portfolio_tracker/prompts.py`.
- Added strict JSON/schema instructions for the four vector agents.
- Added vector agent factories using `gemini-2.5-flash` for performance, fundamentals, sentiment, and macro outputs.
- Added CIO agent instructions using `gemini-2.5-pro` focused on long-term capital preservation, risks, and data gaps.
- Added Critic agent instructions using `gemini-2.5-flash` focused on speculation, guaranteed returns, grounding, risks, and disclaimer checks.
- Added a reusable `GeminiJsonAgent` wrapper that requests JSON output and validates responses into Pydantic schemas.

## Codebase changes

- Added `src/portfolio_tracker/prompts.py`.
- Added `src/portfolio_tracker/agents/base.py`.
- Added vector agent factory modules:
  - `src/portfolio_tracker/agents/performance.py`
  - `src/portfolio_tracker/agents/fundamentals.py`
  - `src/portfolio_tracker/agents/sentiment.py`
  - `src/portfolio_tracker/agents/macro.py`
- Added synthesis/review agent factory modules:
  - `src/portfolio_tracker/agents/cio.py`
  - `src/portfolio_tracker/agents/critic.py`
- Added `tests/unit/test_prompts.py`.
- Added `tests/unit/test_agent_wrappers.py`.
- Updated the revised implementation plan checkboxes for completed Phase 6 items.

## Tests created

- `tests/unit/test_prompts.py`
  - `test_vector_prompts_require_schema_bound_json`
  - `test_cio_and_critic_prompts_contain_investment_guardrails`
- `tests/unit/test_agent_wrappers.py`
  - `test_vector_agent_factories_use_flash_and_parse_schema_outputs`
  - `test_cio_agent_uses_pro_model_and_parses_investment_memo`
  - `test_critic_agent_uses_flash_model_and_parses_critic_result`
  - `test_agent_accepts_plain_json_response_text`

## Additional decisions

- Agent wrappers are thin and SDK-shaped around `client.models.generate_content`, but tests inject fake clients so no live Gemini calls occur.
- `GeminiJsonAgent` uses `response_mime_type="application/json"` and each Pydantic model's JSON schema as `response_schema`.
- Actual ADK graph/node wiring is deferred to Phase 7; Phase 6 only defines prompt and model/schema-bound wrappers.
- The wrappers parse `response.text` as JSON and validate with Pydantic, keeping output contract enforcement deterministic.
- Model selection uses a price/performance split: `gemini-2.5-flash` for high-volume vector and critic calls, and `gemini-2.5-pro` only for CIO synthesis where deeper cross-vector reasoning is worth the higher cost.

## Commit message

`feat: add schema-bound Gemini agent wrappers`
