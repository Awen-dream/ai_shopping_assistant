from app.agents.recommendation_agent import RecommendationAgent
from app.domains.recommendation.service import recommend_with_agent


def test_recommendation_domain_service_preserves_expected_top_result():
    agent = RecommendationAgent()

    results = recommend_with_agent(agent, "Apple 轻薄笔记本 预算12000")

    assert results
    assert results[0]["name"] == "MacBook Air M3"
    assert results[0]["pipeline"]["stage"] == "recommended"
    assert results[0]["matched_features"]["brand_match"] is True
