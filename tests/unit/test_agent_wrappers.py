from __future__ import annotations

import json

from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.agents.cio import create_cio_agent
from portfolio_tracker.agents.critic import create_critic_agent
from portfolio_tracker.agents.fundamentals import create_fundamental_agent
from portfolio_tracker.agents.macro import create_macro_agent
from portfolio_tracker.agents.performance import create_performance_agent
from portfolio_tracker.agents.sentiment import create_sentiment_agent
from portfolio_tracker.schemas import (
    CriticResult,
    DataSourceStatus,
    FundamentalAnalysis,
    InvestmentMemo,
    MacroAnalysis,
    PerformanceAnalysis,
    SentimentAnalysis,
)


def test_vector_agent_factories_use_flash_and_parse_schema_outputs() -> None:
    cases = [
        (
            create_performance_agent,
            {
                "ticker": "MSFT",
                "status": "success",
                "warnings": [],
                "period_years": 10,
                "cagr_10yr": 0.12,
                "max_drawdown": -0.25,
            },
            PerformanceAnalysis,
        ),
        (
            create_fundamental_agent,
            {
                "ticker": "MSFT",
                "status": "success",
                "warnings": [],
                "filing_years": [2023],
            },
            FundamentalAnalysis,
        ),
        (
            create_sentiment_agent,
            {
                "ticker": "MSFT",
                "status": "success",
                "warnings": [],
                "management_confidence": "Neutral",
            },
            SentimentAnalysis,
        ),
        (
            create_macro_agent,
            {
                "ticker": "MSFT",
                "status": "success",
                "warnings": [],
                "macro_headwinds": ["Supply chain risk"],
            },
            MacroAnalysis,
        ),
    ]

    for factory, payload, schema in cases:
        client = FakeGeminiClient(json.dumps(payload))
        agent = factory(client=client)

        result = agent.run({"ticker": "MSFT"})

        assert isinstance(result, schema)
        assert agent.model == "gemini-2.5-flash"
        assert client.calls[0]["config"]["response_mime_type"] == "application/json"


def test_cio_agent_uses_pro_model_and_parses_investment_memo() -> None:
    payload = {
        "ticker": "MSFT",
        "recommendation_summary": "Durable compounder with valuation risk.",
        "long_term_thesis": "Cash generation supports long-term reinvestment.",
        "supporting_evidence": {"macro": ["Regulatory scrutiny"]},
        "key_risks": ["Regulatory pressure"],
        "data_gaps": [],
        "not_investment_advice_disclaimer": "This is not investment advice.",
        "revision_count": 0,
    }
    client = FakeGeminiClient(json.dumps(payload))
    agent = create_cio_agent(client=client)

    result = agent.run({"ticker": "MSFT"})

    assert isinstance(result, InvestmentMemo)
    assert agent.model == "gemini-2.5-pro"


def test_critic_agent_uses_flash_model_and_parses_critic_result() -> None:
    client = FakeGeminiClient(
        json.dumps({"passed": False, "feedback": ["Add risks"], "failed_checks": ["risks"], "grounding_score": 0.6})
    )
    agent = create_critic_agent(client=client)

    result = agent.run({"memo": "draft"})

    assert isinstance(result, CriticResult)
    assert result.failed_checks == ["risks"]
    assert agent.model == "gemini-2.5-flash"


def test_agent_accepts_plain_json_response_text() -> None:
    client = FakeGeminiClient(
        '{"ticker":"MSFT","status":"failed","warnings":[],"period_years":10}'
    )
    agent = GeminiJsonAgent(
        name="test",
        model="gemini-2.5-flash",
        prompt="Return strict JSON",
        output_schema=PerformanceAnalysis,
        client=client,
    )

    result = agent.run("input")

    assert result.status is DataSourceStatus.FAILED


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeModels:
    def __init__(self, parent: FakeGeminiClient) -> None:
        self._parent = parent

    def generate_content(self, **kwargs: object) -> FakeResponse:
        self._parent.calls.append(kwargs)
        return FakeResponse(self._parent.response_text)


class FakeGeminiClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []
        self.models = FakeModels(self)
