from portfolio_tracker.agents.base import GeminiJsonAgent
from portfolio_tracker.prompts import SENTIMENT_AGENT_PROMPT, VECTOR_AGENT_MODEL
from portfolio_tracker.schemas import SentimentAnalysis


def create_sentiment_agent(*, client) -> GeminiJsonAgent[SentimentAnalysis]:
    return GeminiJsonAgent(
        name="sentiment",
        model=VECTOR_AGENT_MODEL,
        prompt=SENTIMENT_AGENT_PROMPT,
        output_schema=SentimentAnalysis,
        client=client,
    )
