"""Command-line demo entrypoint for the Market Signal Synthesizer."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from portfolio_tracker.schemas import (
    DataSourceStatus,
    FundamentalAnalysis,
    InvestmentMemo,
    MacroAnalysis,
    PerformanceAnalysis,
    SentimentAnalysis,
    SynthesizerInput,
    TickerRequest,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        request = TickerRequest(ticker=args.ticker)
    except ValidationError as exc:
        print(f"invalid ticker: {exc.errors()[0]['msg']}", file=sys.stderr)
        return 2

    if not args.mock:
        print("live mode is not implemented yet; rerun with --mock", file=sys.stderr)
        return 2

    synthesizer_input = build_mock_synthesizer_input(request.ticker)
    memo = build_mock_memo(synthesizer_input)
    warnings = _collect_warning_lines(synthesizer_input, memo)

    if args.format == "json":
        print(json.dumps(memo.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(format_markdown_memo(memo))

    if warnings:
        print("Data warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)
    return 0


def build_mock_synthesizer_input(ticker: str) -> SynthesizerInput:
    """Build an offline demo payload from local fixture files."""

    fixtures = _fixture_dir()
    price_fixture = json.loads((fixtures / "price_history_sample.json").read_text())
    filing_fixture = json.loads((fixtures / "sec_filing_summary_sample.json").read_text())
    macro_fixture = json.loads((fixtures / "macro_news_sample.json").read_text())
    transcript_fixture = (fixtures / "transcript_qa_sample.txt").read_text()

    closes = [entry["adj_close"] for entry in price_fixture["history"]]
    cagr = (closes[-1] / closes[0]) ** (1 / 10) - 1
    filings = filing_fixture["filings"]
    risk_factors = [risk for filing in filings for risk in filing.get("risk_factors", [])]
    articles = macro_fixture["articles"]

    return SynthesizerInput(
        ticker=ticker,
        performance=PerformanceAnalysis(
            ticker=ticker,
            status=DataSourceStatus.SUCCESS,
            warnings=[],
            period_years=10,
            cagr_10yr=round(cagr, 3),
            max_drawdown=-0.35,
            dividend_consistency="Dividends recorded across sample period",
        ),
        fundamentals=FundamentalAnalysis(
            ticker=ticker,
            status=DataSourceStatus.SUCCESS,
            warnings=[],
            filing_years=[filing["fiscal_year"] for filing in filings],
            revenue_trajectory=filings[0]["summary"],
            debt_profile="No acute debt concern identified in the mock fixture.",
            fundamental_red_flags=risk_factors,
        ),
        sentiment=SentimentAnalysis(
            ticker=ticker,
            status=DataSourceStatus.PARTIAL,
            warnings=["Mock transcript includes Q&A excerpt only"],
            quarter="Q&A excerpt",
            year=2024,
            management_confidence="Neutral",
            capital_allocation_plans=["Balance AI infrastructure investment with buybacks and dividends"],
            analyst_concerns=["Cloud optimization behavior during macro uncertainty"]
            if "optimization behavior" in transcript_fixture
            else [],
        ),
        macro=MacroAnalysis(
            ticker=ticker,
            status=DataSourceStatus.SUCCESS,
            warnings=[],
            regulatory_environment=articles[0]["summary"],
            macro_headwinds=[article["title"] for article in articles],
            competitive_shifts=["Cloud infrastructure competition remains intense"],
            source_urls=[article["url"] for article in articles],
        ),
    )


def build_mock_memo(synthesizer_input: SynthesizerInput) -> InvestmentMemo:
    gaps = [
        "Sentiment data partially available: Mock transcript includes Q&A excerpt only"
        if synthesizer_input.sentiment.status is DataSourceStatus.PARTIAL
        else ""
    ]
    return InvestmentMemo(
        ticker=synthesizer_input.ticker,
        recommendation_summary="Long-term quality signals are constructive, but regulatory and infrastructure risks remain material.",
        long_term_thesis=(
            "The mock evidence points to durable cloud and productivity software demand, supported by historical "
            "growth and continuing reinvestment capacity. The thesis depends on sustained enterprise demand, "
            "disciplined AI infrastructure spending, and manageable regulatory outcomes."
        ),
        supporting_evidence={
            "performance": ["Positive long-term price trend in fixture history"],
            "fundamentals": synthesizer_input.fundamentals.filing_years,
            "sentiment": synthesizer_input.sentiment.analyst_concerns,
            "macro": synthesizer_input.macro.source_urls,
        },
        key_risks=[
            "Regulatory scrutiny of cloud and software bundling",
            "AI infrastructure supply chain constraints",
            "Enterprise cloud optimization during macro uncertainty",
        ],
        data_gaps=[gap for gap in gaps if gap],
        not_investment_advice_disclaimer="This is not investment advice.",
        revision_count=0,
    )


def format_markdown_memo(memo: InvestmentMemo) -> str:
    sections = [
        f"# Investment Memo: {memo.ticker}",
        "## Recommendation Summary",
        memo.recommendation_summary,
        "## Long-Term Thesis",
        memo.long_term_thesis,
        "## Key Risks",
        _format_bullets(memo.key_risks),
        "## Data Gaps",
        _format_bullets(memo.data_gaps) if memo.data_gaps else "None disclosed.",
        "## Disclaimer",
        memo.not_investment_advice_disclaimer,
    ]
    return "\n\n".join(sections)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="portfolio-tracker")
    parser.add_argument("ticker", help="stock ticker symbol, e.g. MSFT")
    parser.add_argument("--mock", action="store_true", help="run offline using bundled mock fixture semantics")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="output format")
    return parser


def _collect_warning_lines(synthesizer_input: SynthesizerInput, memo: InvestmentMemo) -> list[str]:
    warnings: list[str] = []
    for label, vector in (
        ("Performance", synthesizer_input.performance),
        ("Fundamental", synthesizer_input.fundamentals),
        ("Sentiment", synthesizer_input.sentiment),
        ("Macro", synthesizer_input.macro),
    ):
        for warning in vector.warnings:
            warnings.append(f"{label}: {warning}")
    warnings.extend(memo.data_gaps)
    return warnings


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _fixture_dir() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "tests" / "fixtures"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
