from app.agents.recommendation_agent import RecommendationAgent


def test_recommendation_filters_earphones():
    agent = RecommendationAgent()

    results = agent.recommend("降噪耳机")

    assert results
    assert all(item["category"] == "耳机" for item in results)


def test_recommendation_reason_is_not_empty():
    agent = RecommendationAgent()

    results = agent.recommend("轻薄笔记本")

    assert results
    assert all(item["reason"] for item in results)
