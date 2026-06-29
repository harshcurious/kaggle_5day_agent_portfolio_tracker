from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.prompts import CRITIC_AGENT_MODEL, CRITIC_AGENT_PROMPT
from portfolio_tracker.schemas import CriticResult


def create_critic_agent(*, client) -> GeminiJsonAgent[CriticResult]:
    return GeminiJsonAgent(
        name="critic",
        model=CRITIC_AGENT_MODEL,
        prompt=CRITIC_AGENT_PROMPT,
        output_schema=CriticResult,
        client=client,
    )
