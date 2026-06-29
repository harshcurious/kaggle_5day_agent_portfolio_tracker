from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_tracker.schemas import DataSourceStatus
from portfolio_tracker.tools.edgar_tools import (
    EdgarAdapter,
    extract_bounded_filing_context,
    summarize_fundamentals,
)


FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_summarize_fundamentals_uses_mocked_10k_fixture() -> None:
    fixture = json.loads((FIXTURES / "sec_filing_summary_sample.json").read_text())
    filings = [
        FakeFiling(
            fiscal_year=item["fiscal_year"],
            text=(
                f"Item 7. {item['summary']} Revenue was {item['revenue_usd_millions']} million. "
                f"Net income was {item['net_income_usd_millions']} million. "
                f"Debt remained manageable. Risk factors: {', '.join(item['risk_factors'])}. "
                "Item 8. Consolidated financial statements show durable profitability."
            ),
        )
        for item in fixture["filings"]
    ]
    adapter = EdgarAdapter(company_factory=lambda ticker: FakeCompany(fixture["cik"], filings))

    result = summarize_fundamentals("msft", adapter=adapter)

    assert result.ticker == "MSFT"
    assert result.status is DataSourceStatus.SUCCESS
    assert result.filing_years == [2023, 2022]
    assert "Cloud services" in result.revenue_trajectory
    assert "manageable" in result.debt_profile
    assert "Regulatory scrutiny of digital markets" in result.fundamental_red_flags


def test_extract_bounded_filing_context_keeps_text_under_limit() -> None:
    filing = FakeFiling(
        fiscal_year=2023,
        text="Item 7. " + ("Management discussion. " * 1_000) + "Item 8. Financial statements.",
    )

    context = extract_bounded_filing_context(filing, max_chars=1_000)

    assert len(context) <= 1_000
    assert "Item 7" in context


def test_summarize_fundamentals_missing_filings_returns_partial_warning() -> None:
    adapter = EdgarAdapter(company_factory=lambda ticker: FakeCompany("0000000000", []))

    result = summarize_fundamentals("AAPL", adapter=adapter)

    assert result.status is DataSourceStatus.PARTIAL
    assert result.filing_years == []
    assert "No 10-K filings returned" in result.warnings


def test_adapter_queries_three_recent_10ks_and_exposes_cik() -> None:
    filings = [FakeFiling(2024), FakeFiling(2023), FakeFiling(2022), FakeFiling(2021)]
    company = FakeCompany("0000320193", filings)
    adapter = EdgarAdapter(company_factory=lambda ticker: company)

    result = adapter.get_recent_10k_filings("aapl", limit=3)

    assert result.cik == "0000320193"
    assert [filing.fiscal_year for filing in result.filings] == [2024, 2023, 2022]
    assert company.requested_forms == ["10-K"]


def test_adapter_does_not_mask_sec_provider_exceptions() -> None:
    adapter = EdgarAdapter(company_factory=lambda ticker: ExplodingCompany())

    with pytest.raises(TimeoutError):
        adapter.get_recent_10k_filings("MSFT")


class FakeCompany:
    def __init__(self, cik: str, filings: list[FakeFiling]) -> None:
        self.cik = cik
        self._filings = filings
        self.requested_forms: list[str] = []

    def get_filings(self, *, form: str):
        self.requested_forms.append(form)
        return self._filings


class FakeFiling:
    def __init__(
        self,
        fiscal_year: int,
        text: str = "Item 7. Revenue grew. Debt was stable. Item 8. Financial statements.",
    ) -> None:
        self.fiscal_year = fiscal_year
        self.filing_date = f"{fiscal_year}-01-31"
        self.form = "10-K"
        self.homepage_url = f"https://www.sec.gov/Archives/{fiscal_year}"
        self._text = text

    def text(self) -> str:
        return self._text


class ExplodingCompany:
    cik = "0000000000"

    def get_filings(self, *, form: str):
        raise TimeoutError("temporary SEC block")
