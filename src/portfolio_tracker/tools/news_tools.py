"""Macro and regulatory news grounding tools."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any, Protocol

from portfolio_tracker.config import Settings, load_settings
from portfolio_tracker.schemas import DataSourceStatus, MacroAnalysis, TickerRequest


Article = dict[str, Any]


class _SearchProvider(Protocol):
    def __call__(self, query: str) -> list[Article]: ...


class _GoogleGroundingProvider(Protocol):
    def __call__(self, query: str, *, api_key: str) -> list[Article]: ...


class MacroNewsAdapter:
    """Search adapter that keeps provider calls swappable and exceptions visible."""

    def __init__(self, *, provider: _SearchProvider) -> None:
        self._provider = provider

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        google_grounding_provider: _GoogleGroundingProvider | None = None,
        fallback_provider: _SearchProvider | None = None,
    ) -> "MacroNewsAdapter":
        settings = settings or load_settings()
        fallback_provider = fallback_provider or _empty_search_provider
        if settings.google_api_key and google_grounding_provider:
            return cls(
                provider=lambda query: google_grounding_provider(
                    query, api_key=settings.google_api_key or ""
                )
            )
        return cls(provider=fallback_provider)

    def search(self, query: str) -> list[Article]:
        return self._provider(query)


def build_macro_search_queries(ticker: str) -> list[str]:
    normalized_ticker = TickerRequest(ticker=ticker).ticker
    noise_filters = '-stock -shares -"price action"'
    return [
        f"{normalized_ticker} antitrust litigation regulatory risk {noise_filters}",
        f"{normalized_ticker} supply chain risk macro headwinds {noise_filters}",
        f"{normalized_ticker} competitive shifts industry disruption {noise_filters}",
    ]


def analyze_macro_news(
    ticker: str,
    *,
    adapter: MacroNewsAdapter | None = None,
) -> MacroAnalysis:
    normalized_ticker = TickerRequest(ticker=ticker).ticker
    adapter = adapter or MacroNewsAdapter.from_settings()
    articles: list[Article] = []
    for query in build_macro_search_queries(normalized_ticker):
        articles.extend(adapter.search(query))

    filtered_articles = _dedupe_articles(filter_long_term_news(articles))
    if not filtered_articles:
        return MacroAnalysis(
            ticker=normalized_ticker,
            status=DataSourceStatus.PARTIAL,
            warnings=["No long-term macro or regulatory news returned"],
        )

    return MacroAnalysis(
        ticker=normalized_ticker,
        status=DataSourceStatus.SUCCESS,
        regulatory_environment=_summarize_topic(filtered_articles, ["regulation", "regulatory", "antitrust"]),
        macro_headwinds=_summarize_list(filtered_articles, ["macro", "supply chain", "inflation", "rates"]),
        competitive_shifts=_summarize_list(filtered_articles, ["competitive", "competition", "industry", "disruption"]),
        source_urls=[str(article["url"]) for article in filtered_articles if article.get("url")],
    )


def filter_long_term_news(articles: Iterable[Article]) -> list[Article]:
    return [article for article in articles if _is_long_term_article(article)]


def load_fixture_articles(path: str | Path) -> list[Article]:
    payload = json.loads(Path(path).read_text())
    return list(payload.get("articles", []))


def _empty_search_provider(query: str) -> list[Article]:
    return []


def _is_long_term_article(article: Article) -> bool:
    haystack = _article_text(article)
    noise_terms = ["stock rises", "stock falls", "shares gain", "shares fall", "price action"]
    if any(term in haystack for term in noise_terms):
        return False
    signal_terms = [
        "regulat",
        "antitrust",
        "supply chain",
        "macro",
        "litigation",
        "competitive",
        "competition",
        "infrastructure",
    ]
    return any(term in haystack for term in signal_terms)


def _article_text(article: Article) -> str:
    topics = article.get("topics") or []
    return " ".join(
        [
            str(article.get("title", "")),
            str(article.get("summary", "")),
            " ".join(str(topic) for topic in topics),
        ]
    ).lower()


def _dedupe_articles(articles: Iterable[Article]) -> list[Article]:
    seen_urls: set[str] = set()
    deduped: list[Article] = []
    for article in articles:
        url = str(article.get("url", ""))
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduped.append(article)
    return deduped


def _summarize_topic(articles: list[Article], keywords: list[str]) -> str | None:
    summaries = _summarize_list(articles, keywords)
    return " ".join(summaries) if summaries else None


def _summarize_list(articles: list[Article], keywords: list[str]) -> list[str]:
    matches: list[str] = []
    for article in articles:
        text = _article_text(article)
        if any(keyword in text for keyword in keywords):
            title = str(article.get("title") or "").strip()
            summary_text = str(article.get("summary") or "").strip()
            summary = f"{title}: {summary_text}".strip(": ")
            if summary:
                matches.append(summary)
    return matches[:5]
