# Phase 5 — Macro / News Grounding Tool

## Completed plan steps

- Implemented `MacroNewsAdapter` behind a provider interface.
- Added Google-grounding provider selection when a Google API key and provider callable are available.
- Added fallback provider support when Google grounding is unavailable.
- Added fixture article loading for offline tests and demo-mode providers.
- Defined targeted long-term macro/regulatory search queries.
- Added negative query terms to avoid daily price-action content.
- Implemented filtering that removes stock-price noise articles and keeps regulatory, macro, supply-chain, competition, and infrastructure signals.
- Captured source URLs in the final `MacroAnalysis` payload.

## Codebase changes

- Added `src/portfolio_tracker/tools/news_tools.py`.
- Added `tests/unit/test_news_tools.py`.
- Updated the revised implementation plan checkboxes for completed Phase 5 items.

## Tests created

- `tests/unit/test_news_tools.py`
  - `test_build_macro_search_queries_include_long_term_risk_keywords_and_noise_filters`
  - `test_filter_long_term_news_excludes_stock_price_noise`
  - `test_analyze_macro_news_uses_fixture_provider_and_captures_urls`
  - `test_adapter_prefers_google_grounding_when_google_api_key_is_available`
  - `test_adapter_uses_fallback_provider_without_google_api_key`
  - `test_adapter_does_not_mask_provider_exceptions`

## Additional decisions

- Google Search Grounding is represented as an injectable provider callable instead of a hard-coded SDK dependency; this keeps unit tests offline and lets Phase 6+ wire the actual Gemini/grounding implementation.
- The default fallback provider returns an empty list, producing a structured `PARTIAL` result rather than live network access.
- Query construction includes `-stock`, `-shares`, and `-"price action"` noise filters for every query.
- Article summaries include title plus summary so topic labels like supply chain and antitrust remain visible in memo inputs.
- Duplicate article URLs are removed before producing source citations.

## Commit message

`feat: add macro news grounding tool`
