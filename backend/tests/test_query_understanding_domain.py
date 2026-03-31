from app.domains.query_understanding.model import normalize_intent, parse_rule_based_intent


def test_parse_rule_based_intent_extracts_budget_sort_and_fulfillment():
    intent = parse_rule_based_intent("学生用 轻薄本 预算6000 尽快到货 预售也可以 要性价比高一些")

    assert intent["category"] == "笔记本"
    assert intent["budget_range"] == [0, 6000]
    assert intent["sort_preference"] == "price"
    assert intent["scenario"] == "学生"
    assert intent["fulfillment_preference"] == "fast_delivery"
    assert "轻薄" in intent["required_features"]


def test_normalize_intent_promotes_category_to_preferred_categories():
    normalized = normalize_intent(
        {
            "category": "耳机",
            "preferred_categories": [],
            "preferred_brand": "Sony",
            "required_features": "降噪",
        }
    )

    assert normalized["category"] == "耳机"
    assert normalized["preferred_categories"][0] == "耳机"
    assert normalized["preferred_brand"] == ["Sony"]
    assert normalized["required_features"] == ["降噪"]
