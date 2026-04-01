from ...agents.recommendation_agent import RecommendationAgent
from ...agents.search_agent import SearchAgent
from ..pipeline import normalize_pipeline_products
from .model import recommend_products_with_components


def create_recommendation_agent():
    return RecommendationAgent()


def recommend_with_agent(agent: RecommendationAgent, query: str, user_profile: dict | None = None, topk: int = 5):
    return normalize_pipeline_products(
        recommend_products_with_components(
            query,
            user_profile,
            intent_agent=agent.intent_agent,
            category_embedding=agent.category_embedding,
            fallback_category_classifier=agent.category_classifier,
            query_context_builder=agent.query_context_builder,
            ranker=agent.ranker,
            reasoner=agent.reasoner,
            vector_retriever=agent.vector_retriever,
            keyword_retriever=agent.keyword_retriever,
            products=agent.products,
            topk=topk,
        ),
        stage="recommended",
    )


def recommend_products(query: str, user_profile: dict | None = None):
    return recommend_with_agent(create_recommendation_agent(), query, user_profile=user_profile)


def create_search_agent():
    return SearchAgent()


def search_market_offers(products, user_profile: dict | None = None, agent: SearchAgent | None = None):
    return normalize_pipeline_products(
        (agent or create_search_agent()).search(products, user_profile=user_profile),
        stage="searched",
    )
