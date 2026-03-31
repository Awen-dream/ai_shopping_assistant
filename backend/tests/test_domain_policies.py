from app.domains.inventory.model import apply_inventory_policy
from app.domains.pricing.model import compare_product_prices


def test_pricing_policy_applies_student_discount_strategy():
    products = [
        {
            "id": 1,
            "name": "MacBook Air M3",
            "brand": "Apple",
            "category": "笔记本",
            "price": 9999,
            "promotion_tag": "教育优惠",
            "search_results": [
                {
                    "store": "Apple Store",
                    "channel": "official",
                    "merchant_type": "official",
                    "sale_price": 9999,
                    "list_price": 9999,
                    "shipping_days": 2,
                    "service_score": 9.7,
                }
            ],
        }
    ]

    priced = compare_product_prices(
        products,
        user_profile={"scenario": "学生", "price_sensitivity": "high", "sort_preference": "price"},
    )
    best_offer = priced[0]["best_offer"]

    assert best_offer["coupon_discount"] > 0
    assert "学生场景加码" in best_offer["promotion_applied"]
    assert best_offer["price_label"] in {"活动好价", "大促低价"}


def test_inventory_policy_prefers_city_warehouse_and_preserves_fulfillment_fields():
    products = [
        {
            "id": 7,
            "name": "Lenovo Xiaoxin Pro 14",
            "category": "笔记本",
            "promotion_tag": "国补专区",
            "warehouses": [
                {"name": "华北仓", "stock": 18},
                {"name": "华东仓", "stock": 12},
            ],
            "search_results": [
                {
                    "store": "JD Mall",
                    "sale_price": 5299,
                    "price_score": 5299,
                    "shipping_days": 2,
                }
            ],
        }
    ]

    stocked = apply_inventory_policy(products, user_profile={"city": "Hangzhou", "urgency": "urgent"})
    best_offer = stocked[0]["best_offer"]

    assert best_offer["fulfillment_warehouse"] == "华东仓"
    assert best_offer["shipping_days"] == 1
    assert best_offer["purchase_limit"] >= 1
    assert best_offer["estimated_delivery"]
