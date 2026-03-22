from app.agents.intent_agent import IntentAgent
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
    assert any("匹配你要找的笔记本" in item["reason"] for item in results)


def test_recommendation_exposes_match_features():
    agent = RecommendationAgent()

    result = agent.recommend("Apple 轻薄笔记本 预算12000")[0]

    assert result["matched_features"]["brand_match"] is True
    assert result["matched_features"]["budget_match"] is True


def test_hybrid_recall_merges_keyword_and_vector_scores():
    agent = RecommendationAgent()
    product_a = agent.products[0]
    product_b = agent.products[1]

    agent.keyword_retriever.search = lambda query: [(product_a, 3.0)]
    agent.vector_retriever.search = lambda query, topk=20: [(product_a, 0.2), (product_b, 0.8)]

    query_context = agent.query_context_builder.build("苹果电脑", {"budget_range": [0, 20000]})
    candidates = agent.hybrid_recall("苹果电脑", query_context)
    candidates_by_id = {item["product"]["id"]: item for item in candidates}

    assert candidates_by_id[product_a["id"]]["keyword_score"] > 0
    assert candidates_by_id[product_a["id"]]["vector_score"] >= 0
    assert candidates_by_id[product_b["id"]]["vector_score"] > 0


def test_preferred_categories_affect_candidates_when_query_has_no_category():
    agent = RecommendationAgent()

    result = agent.recommend(
        "适合学生的高性价比设备",
        {
            "preferred_brand": ["Lenovo", "Xiaomi"],
            "budget_range": [0, 6000],
            "interests": ["办公", "性价比"],
            "preferred_categories": ["笔记本"],
        },
    )[0]

    assert result["category"] == "笔记本"


def test_intent_agent_extracts_stage3_structured_fields():
    agent = IntentAgent(llm=None)

    intent = agent.parse_intent("学生用 轻薄本 预算6000 尽快到货 要性价比高一些")

    assert intent["scenario"] == "学生"
    assert intent["sort_preference"] == "price"
    assert intent["urgency"] == "urgent"
    assert intent["price_sensitivity"] == "high"
    assert intent["category"] == "笔记本"


def test_recommendation_tracks_required_feature_matches():
    agent = RecommendationAgent()

    result = agent.recommend(
        "通勤降噪耳机",
        {
            "budget_range": [0, 4000],
            "interests": ["降噪"],
            "required_features": ["降噪", "轻薄"],
            "scenario": "通勤",
            "category": "耳机",
        },
    )[0]

    assert result["category"] == "耳机"
    assert result["matched_features"]["matched_required_features"]
