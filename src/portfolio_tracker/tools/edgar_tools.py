"""SEC EDGAR-backed fundamental analysis tools."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import re
from typing import Protocol

from portfolio_tracker.schemas import DataSourceStatus, FundamentalAnalysis, TickerRequest


MAX_FILING_CONTEXT_CHARS = 15_000


class _FilingLike(Protocol):
    fiscal_year: int
    filing_date: str
    form: str
    homepage_url: str

    def text(self) -> str: ...


class _CompanyLike(Protocol):
    cik: str

    def get_filings(self, *, form: str): ...


@dataclass(frozen=True)
class Recent10KFilings:
    ticker: str
    cik: str
    filings: list[_FilingLike]


class EdgarAdapter:
    """Thin EdgarTools adapter that lets SEC/provider exceptions propagate."""

    def __init__(self, company_factory: Callable[[str], _CompanyLike] | None = None) -> None:
        self._company_factory = company_factory or _default_company_factory

    def get_recent_10k_filings(self, ticker: str, *, limit: int = 3) -> Recent10KFilings:
        normalized_ticker = TickerRequest(ticker=ticker).ticker
        company = self._company_factory(normalized_ticker)
        filings = company.get_filings(form="10-K")
        recent_filings = list(filings)[:limit]
        return Recent10KFilings(
            ticker=normalized_ticker,
            cik=str(company.cik),
            filings=recent_filings,
        )


def summarize_fundamentals(
    ticker: str,
    *,
    adapter: EdgarAdapter | None = None,
    filing_limit: int = 3,
    max_context_chars: int = MAX_FILING_CONTEXT_CHARS,
) -> FundamentalAnalysis:
    """Summarize recent 10-K fundamentals into the Phase 1 schema."""

    normalized_ticker = TickerRequest(ticker=ticker).ticker
    adapter = adapter or EdgarAdapter()
    filing_result = adapter.get_recent_10k_filings(normalized_ticker, limit=filing_limit)

    if not filing_result.filings:
        return FundamentalAnalysis(
            ticker=normalized_ticker,
            status=DataSourceStatus.PARTIAL,
            warnings=["No 10-K filings returned"],
            filing_years=[],
        )

    contexts = [
        extract_bounded_filing_context(filing, max_chars=max_context_chars // len(filing_result.filings))
        for filing in filing_result.filings
    ]
    combined_context = "\n\n".join(contexts)[:max_context_chars]

    return FundamentalAnalysis(
        ticker=normalized_ticker,
        status=DataSourceStatus.SUCCESS,
        filing_years=[_filing_year(filing) for filing in filing_result.filings],
        revenue_trajectory=_sentence_for_keywords(combined_context, ["revenue", "sales"]),
        debt_profile=_sentence_for_keywords(combined_context, ["debt", "liabilities"]),
        fundamental_red_flags=_risk_flags(combined_context),
    )


def extract_bounded_filing_context(filing: _FilingLike, *, max_chars: int) -> str:
    """Extract bounded Item 7 / Item 8 filing context without returning raw full filings."""

    text = _normalize_whitespace(filing.text())
    item_7 = _extract_section(text, "Item 7", "Item 8")
    item_8 = _extract_section(text, "Item 8", "Item 9")
    selected = " ".join(part for part in [item_7, item_8] if part).strip() or text
    return selected[:max_chars]


def _default_company_factory(ticker: str) -> _CompanyLike:
    from edgar import Company

    return Company(ticker)


def _filing_year(filing: _FilingLike) -> int:
    if hasattr(filing, "fiscal_year"):
        return int(filing.fiscal_year)
    return int(str(filing.filing_date)[:4])


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_section(text: str, start_label: str, end_label: str) -> str:
    pattern = re.compile(
        rf"({re.escape(start_label)}\.?\s+.*?)(?={re.escape(end_label)}\.?\s+|$)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _sentence_for_keywords(text: str, keywords: Sequence[str]) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    matches = [
        sentence.strip()
        for sentence in sentences
        if any(keyword.lower() in sentence.lower() for keyword in keywords)
    ]
    return " ".join(matches[:3]) or None


def _risk_flags(text: str) -> list[str]:
    explicit_risk_sections = re.findall(
        r"Risk factors:\s*(.*?)(?=\.\s+|$)", text, flags=re.IGNORECASE
    )
    if explicit_risk_sections:
        flags: list[str] = []
        for section in explicit_risk_sections:
            flags.extend(flag.strip(" .") for flag in re.split(r",|;", section) if flag.strip(" ."))
        return flags[:5]

    risk_text = _sentence_for_keywords(text, ["risk", "competition", "regulatory", "cybersecurity"])
    return [risk_text] if risk_text else []
