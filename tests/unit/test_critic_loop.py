import asyncio

from portfolio_tracker.schemas import CriticResult, InvestmentMemo
from portfolio_tracker.workflow import run_critic_guardrail_loop


def memo(**overrides) -> InvestmentMemo:
    payload = {
        "ticker": "MSFT",
        "recommendation_summary": "Durable compounder with valuation risk.",
        "long_term_thesis": "Long-term thesis is supported by cash generation and reinvestment capacity.",
        "supporting_evidence": {"performance": ["Positive 10-year CAGR"]},
        "key_risks": ["Regulatory scrutiny"],
        "data_gaps": [],
        "not_investment_advice_disclaimer": "This is not investment advice.",
        "revision_count": 0,
    }
    payload.update(overrides)
    return InvestmentMemo(**payload)


def test_speculatory_language_routes_back_to_cio_before_invoking_critic() -> None:
    initial = memo(recommendation_summary="Guaranteed return with no risk for long-term holders.")
    cio = FakeCioAgent([memo(revision_count=1)])
    critic = FakeCriticAgent([CriticResult(passed=True, grounding_score=1.0)])

    result = asyncio.run(run_critic_guardrail_loop(initial, cio_agent=cio, critic_agent=critic))

    assert result.output.revision_count == 1
    assert critic.inputs[0]["memo"]["revision_count"] == 1
    assert cio.inputs[0]["feedback"] == [
        "Remove prohibited speculative language: guaranteed return",
        "Remove prohibited speculative language: no risk",
    ]


def test_missing_risks_routes_back_to_cio_before_invoking_critic() -> None:
    initial = memo(key_risks=[])
    cio = FakeCioAgent([memo(key_risks=["Competition"], revision_count=1)])
    critic = FakeCriticAgent([CriticResult(passed=True, grounding_score=1.0)])

    result = asyncio.run(run_critic_guardrail_loop(initial, cio_agent=cio, critic_agent=critic))

    assert result.output.key_risks == ["Competition"]
    assert critic.inputs[0]["memo"]["revision_count"] == 1
    assert cio.inputs[0]["failed_checks"] == ["key_risks"]


def test_passing_deterministic_checks_invokes_llm_critic() -> None:
    initial = memo()
    cio = FakeCioAgent([])
    critic = FakeCriticAgent([CriticResult(passed=True, grounding_score=0.9)])

    result = asyncio.run(run_critic_guardrail_loop(initial, cio_agent=cio, critic_agent=critic))

    assert result.output == initial
    assert len(critic.inputs) == 1
    assert cio.inputs == []


def test_infinite_rewrite_loop_terminates_after_two_revisions_with_warning() -> None:
    initial = memo(key_risks=[])
    first_revision = memo(key_risks=[], revision_count=1)
    second_revision = memo(key_risks=[], revision_count=2)
    cio = FakeCioAgent([first_revision, second_revision, memo(revision_count=3)])
    critic = FakeCriticAgent([])

    result = asyncio.run(run_critic_guardrail_loop(initial, cio_agent=cio, critic_agent=critic, max_revisions=2))

    assert result.output.revision_count == 2
    assert result.output.recommendation_summary.startswith("GUARDRAIL WARNING: ")
    assert len(cio.inputs) == 2
    assert critic.inputs == []


class FakeCioAgent:
    def __init__(self, responses: list[InvestmentMemo]) -> None:
        self.responses = responses
        self.inputs: list[dict] = []

    def run(self, input_payload: dict) -> InvestmentMemo:
        self.inputs.append(input_payload)
        return self.responses.pop(0)


class FakeCriticAgent:
    def __init__(self, responses: list[CriticResult]) -> None:
        self.responses = responses
        self.inputs: list[dict] = []

    def run(self, input_payload: dict) -> CriticResult:
        self.inputs.append(input_payload)
        return self.responses.pop(0)
