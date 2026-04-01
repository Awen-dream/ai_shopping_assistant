from ...agents.intent_agent import IntentAgent
from ..pipeline import normalize_intent_profile


def create_intent_agent(llm=None):
    return IntentAgent(llm=llm)


def parse_query_intent(query: str, llm=None) -> dict:
    return normalize_intent_profile(create_intent_agent(llm=llm).parse_intent(query), raw_query=query)
