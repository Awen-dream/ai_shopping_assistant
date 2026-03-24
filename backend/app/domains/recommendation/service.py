from ...agents.recommendation_agent import RecommendationAgent
from ...agents.search_agent import SearchAgent


def create_recommendation_agent():
    return RecommendationAgent()


def recommend_products(query: str, user_profile: dict | None = None):
    return create_recommendation_agent().recommend(query, user_profile)


def create_search_agent():
    return SearchAgent()


def search_market_offers(products, user_profile: dict | None = None):
    return create_search_agent().search(products, user_profile=user_profile)
