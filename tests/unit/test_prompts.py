from __future__ import annotations

from portfolio_tracker import prompts


def test_vector_prompts_require_schema_bound_json() -> None:
    prompt_text = "\n".join(
        [
            prompts.PERFORMANCE_AGENT_PROMPT,
            prompts.FUNDAMENTAL_AGENT_PROMPT,
            prompts.SENTIMENT_AGENT_PROMPT,
            prompts.MACRO_AGENT_PROMPT,
        ]
    ).lower()

    assert "strict json" in prompt_text
    assert "schema" in prompt_text
    assert "no markdown" in prompt_text
    assert "gemini-2.5-flash" in prompt_text


def test_cio_and_critic_prompts_contain_investment_guardrails() -> None:
    combined = f"{prompts.CIO_AGENT_PROMPT}\n{prompts.CRITIC_AGENT_PROMPT}".lower()

    assert "no price targets" in combined
    assert "no short-term speculation" in combined
    assert "key risks" in combined
    assert "not investment advice" in combined
    assert "guaranteed returns" in combined
    assert "grounding" in combined
    assert "gemini-2.5-pro" in prompts.CIO_AGENT_PROMPT.lower()
    assert "gemini-2.5-flash" in prompts.CRITIC_AGENT_PROMPT.lower()
