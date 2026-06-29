from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_tracker.config import Settings
from portfolio_tracker.schemas import DataSourceStatus
from portfolio_tracker.tools.news_tools import (
    MacroNewsAdapter,
    analyze_macro_news,
    build_macro_search_queries,
    filter_long_term_news,
    load_fixture_articles,
)


FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_build_macro_search_queries_include_long_term_risk_keywords_and_noise_filters() -> None:
    queries = build_macro_search_queries("msft")

    joined = " ".join(queries).lower()

    assert "msft antitrust litigation" in joined
    assert "msft supply chain risk" in joined
    assert "regulatory" in joined
    assert "competitive" in joined
    assert "-stock" in joined
    assert "-shares" in joined
    assert '"price action"' in joined


def test_filter_long_term_news_excludes_stock_price_noise() -> None:
    articles = [
        {
            "title": "MSFT stock rises as shares gain after analyst upgrade",
            "url": "https://example.com/stock-price-noise",
            "summary": "Daily stock price action dominated trading.",
            "topics": ["stock", "shares"],
        },
        {
            "title": "Regulators examine cloud software bundling practices",
            "url": "https://example.com/regulatory-cloud-bundling",
            "summary": "Antitrust agencies are reviewing cloud software bundling practices.",
            "topics": ["regulation", "antitrust"],
        },
    ]

    filtered = filter_long_term_news(articles)

    assert [article["url"] for article in filtered] == [
        "https://example.com/regulatory-cloud-bundling"
    ]


def test_analyze_macro_news_uses_fixture_provider_and_captures_urls() -> None:
    fixture_articles = load_fixture_articles(FIXTURES / "macro_news_sample.json")
    adapter = MacroNewsAdapter(provider=lambda query: fixture_articles)

    result = analyze_macro_news("msft", adapter=adapter)

    assert result.ticker == "MSFT"
    assert result.status is DataSourceStatus.SUCCESS
    assert "antitrust" in result.regulatory_environment.lower()
    assert "supply chain" in " ".join(result.macro_headwinds).lower()
    assert "https://example.com/regulatory-cloud-bundling" in result.source_urls
    assert "https://example.com/ai-server-supply-chain" in result.source_urls


def test_adapter_prefers_google_grounding_when_google_api_key_is_available() -> None:
    calls: list[dict[str, object]] = []

    def google_provider(query: str, *, api_key: str) -> list[dict[str, object]]:
        calls.append({"query": query, "api_key": api_key})
        return []

    adapter = MacroNewsAdapter.from_settings(
        Settings(google_api_key="google-key"),
        google_grounding_provider=google_provider,
        fallback_provider=lambda query: pytest.fail("fallback should not be used"),
    )

    adapter.search("MSFT regulatory risk -stock")

    assert calls == [{"query": "MSFT regulatory risk -stock", "api_key": "google-key"}]


def test_adapter_uses_fallback_provider_without_google_api_key() -> None:
    calls: list[str] = []
    adapter = MacroNewsAdapter.from_settings(
        Settings(google_api_key=None),
        google_grounding_provider=lambda query, api_key: pytest.fail("google should not be used"),
        fallback_provider=lambda query: calls.append(query) or [],
    )

    adapter.search("MSFT macro risk -stock")

    assert calls == ["MSFT macro risk -stock"]


def test_adapter_does_not_mask_provider_exceptions() -> None:
    adapter = MacroNewsAdapter(provider=lambda query: (_ for _ in ()).throw(TimeoutError("search")))

    with pytest.raises(TimeoutError):
        adapter.search("MSFT regulatory risk")
