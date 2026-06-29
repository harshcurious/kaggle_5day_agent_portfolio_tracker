from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.prompts import PERFORMANCE_AGENT_PROMPT, VECTOR_AGENT_MODEL
from portfolio_tracker.schemas import PerformanceAnalysis


def create_performance_agent(*, client) -> GeminiJsonAgent[PerformanceAnalysis]:
    return GeminiJsonAgent(
        name="performance",
        model=VECTOR_AGENT_MODEL,
        prompt=PERFORMANCE_AGENT_PROMPT,
        output_schema=PerformanceAnalysis,
        client=client,
    )
