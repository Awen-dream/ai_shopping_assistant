from ...agents.intent_agent import IntentAgent


def create_intent_agent(llm=None):
    return IntentAgent(llm=llm)


def parse_query_intent(query: str, llm=None) -> dict:
    return create_intent_agent(llm=llm).parse_intent(query)
