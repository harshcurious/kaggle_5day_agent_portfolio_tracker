from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.prompts import CIO_AGENT_MODEL, CIO_AGENT_PROMPT
from portfolio_tracker.schemas import InvestmentMemo


def create_cio_agent(*, client) -> GeminiJsonAgent[InvestmentMemo]:
    return GeminiJsonAgent(
        name="cio",
        model=CIO_AGENT_MODEL,
        prompt=CIO_AGENT_PROMPT,
        output_schema=InvestmentMemo,
        client=client,
    )
