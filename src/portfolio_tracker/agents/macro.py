from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.prompts import MACRO_AGENT_PROMPT, VECTOR_AGENT_MODEL
from portfolio_tracker.schemas import MacroAnalysis


def create_macro_agent(*, client) -> GeminiJsonAgent[MacroAnalysis]:
    return GeminiJsonAgent(
        name="macro",
        model=VECTOR_AGENT_MODEL,
        prompt=MACRO_AGENT_PROMPT,
        output_schema=MacroAnalysis,
        client=client,
    )
