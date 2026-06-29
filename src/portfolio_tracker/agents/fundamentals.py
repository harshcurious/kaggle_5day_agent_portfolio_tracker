from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.prompts import FUNDAMENTAL_AGENT_PROMPT, VECTOR_AGENT_MODEL
from portfolio_tracker.schemas import FundamentalAnalysis


def create_fundamental_agent(*, client) -> GeminiJsonAgent[FundamentalAnalysis]:
    return GeminiJsonAgent(
        name="fundamentals",
        model=VECTOR_AGENT_MODEL,
        prompt=FUNDAMENTAL_AGENT_PROMPT,
        output_schema=FundamentalAnalysis,
        client=client,
    )
