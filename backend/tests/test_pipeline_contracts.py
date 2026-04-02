from app.domains.pipeline import (
    PIPELINE_CONTRACT_VERSION,
    build_safe_product_payload,
    normalize_intent_profile,
    normalize_pipeline_products,
)


def test_normalize_intent_profile_applies_stage3_contract_defaults():
    normalized = normalize_intent_profile(
        {
            "preferred_brand": "Apple",
            "budget_range": ["1000", "5000"],
            "price_sensitivity": None,
            "recent_clicked_product_ids": ["1", "bad", 3],
        },
        raw_query="Apple 手机",
    )

    assert normalized["raw_query"] == "Apple 手机"
    assert normalized["preferred_brand"] == ["Apple"]
    assert normalized["budget_range"] == [1000, 5000]
    assert normalized["recent_clicked_product_ids"] == [1, 3]
    assert normalized["price_sensitivity"] == "medium"
    assert normalized["sort_preference"] == "balanced"
    assert normalized["merchant_preference"] == ""


def test_normalize_pipeline_products_preserves_stage_and_offer_shape():
    normalized = normalize_pipeline_products(
        [
            {
                "id": 99,
                "name": "Demo Product",
                "category": "耳机",
                "price": 999,
                "search_results": [
                    {
                        "store": "JD Mall",
                        "channel": "jd",
                        "sale_price": 899,
                    }
                ],
            }
        ],
        stage="priced",
    )

    assert normalized[0]["pipeline"]["contract_version"] == PIPELINE_CONTRACT_VERSION
    assert normalized[0]["pipeline"]["stage"] == "priced"
    assert normalized[0]["search_results"][0]["channel"] == "jd"
    assert normalized[0]["search_results"][0]["currency"] == "CNY"
    assert normalized[0]["search_results"][0]["strategy_tags"] == []


def test_build_safe_product_payload_keeps_contract_metadata():
    payload = build_safe_product_payload(
        {
            "id": 1,
            "name": "Contract Product",
            "category": "手机",
            "price": 4999,
            "pipeline": {
                "contract_version": PIPELINE_CONTRACT_VERSION,
                "stage": "inventory_ready",
            },
        }
    )

    assert payload["pipeline"]["contract_version"] == PIPELINE_CONTRACT_VERSION
    assert payload["pipeline"]["stage"] == "inventory_ready"
