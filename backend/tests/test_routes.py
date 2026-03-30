from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_multi_agent_task_returns_results_wrapper():
    response = client.get("/multi-agent-task", params={"q": "耳机"})

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert payload["results"]
    assert payload["results"][0]["category"] == "耳机"
    assert payload["results"][0]["best_offer"]["sale_price"] <= payload["results"][0]["price"]
    assert payload["results"][0]["monthly_sales"] > 0


def test_multi_agent_task_rejects_empty_query():
    response = client.get("/multi-agent-task", params={"q": ""})

    assert response.status_code == 422


def test_image_route_falls_back_safely_for_invalid_image_bytes():
    response = client.post(
        "/multi-agent-task/image",
        files={"file": ("not-an-image.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert payload["results"]
    assert payload["results"][0]["reason"]


def test_query_uses_persisted_user_profile():
    response = client.get(
        "/multi-agent-task",
        params={"q": "轻薄本", "user_id": "demo_student"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]
    assert payload["results"][0]["category"] == "笔记本"
    assert payload["results"][0]["price"] <= 6000
    assert payload["results"][0]["best_offer"]["fulfillment_warehouse"] == "华东仓"


def test_behavior_profile_query_prefers_value_laptop_for_student():
    response = client.get(
        "/multi-agent-task",
        params={"q": "性价比笔记本", "user_id": "demo_student"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]
    assert payload["results"][0]["name"] == "Lenovo Xiaoxin Pro 14"
    assert payload["results"][0]["price"] <= 6000


def test_stage3_price_and_inventory_fields_are_exposed():
    response = client.get(
        "/multi-agent-task",
        params={"q": "学生 预算6000 轻薄本 尽快到货"},
    )

    assert response.status_code == 200
    payload = response.json()
    best_offer = payload["results"][0]["best_offer"]
    assert "promotion_applied" in best_offer
    assert "coupon_discount" in best_offer
    assert "fulfillment_type" in best_offer
    assert "purchase_limit" in best_offer
    assert "strategy_tags" in best_offer
    assert "merchant_type" in best_offer


def test_commute_headphones_query_returns_fast_delivery_offer():
    response = client.get(
        "/multi-agent-task",
        params={"q": "通勤降噪耳机"},
    )

    assert response.status_code == 200
    payload = response.json()
    top_result = payload["results"][0]
    assert top_result["name"] == "Sony WH-1000XM5"
    assert "适合通勤场景" in top_result["reason"]
    assert top_result["best_offer"]["channel"] == "jd"
    assert top_result["best_offer"]["shipping_days"] == 1
    assert "通勤快送" in top_result["best_offer"]["strategy_tags"]


def test_camera_phone_query_returns_budget_matched_phone():
    response = client.get(
        "/multi-agent-task",
        params={"q": "拍照手机 预算5000"},
    )

    assert response.status_code == 200
    payload = response.json()
    top_result = payload["results"][0]
    assert top_result["name"] == "Xiaomi 14"
    assert top_result["price"] <= 5000
    assert "适合摄影场景" in top_result["reason"]
    assert top_result["best_offer"]["price_label"] in {"活动好价", "大促低价"}


def test_brand_query_prefers_apple_laptop_in_budget():
    response = client.get(
        "/multi-agent-task",
        params={"q": "Apple 轻薄笔记本 预算12000"},
    )

    assert response.status_code == 200
    payload = response.json()
    top_result = payload["results"][0]
    assert top_result["name"] == "MacBook Air M3"
    assert top_result["matched_features"]["brand_match"] is True
    assert top_result["matched_features"]["budget_match"] is True


def test_user_profile_crud_roundtrip():
    save_response = client.put(
        "/user-profiles/test_stage2_user",
        json={
            "preferred_brand": ["Apple"],
            "favorite_brands": ["Apple"],
            "budget_range": [1000, 9000],
            "interests": ["轻便"],
            "preferred_categories": ["手机", "耳机"],
            "recent_categories": ["手机"],
            "recent_clicked_product_ids": [1, 2],
            "price_band_preference": "premium",
            "city": "Suzhou",
        },
    )

    assert save_response.status_code == 200
    saved_profile = save_response.json()["profile"]
    assert saved_profile["preferred_brand"] == ["Apple"]
    assert saved_profile["recent_clicked_product_ids"] == [1, 2]

    read_response = client.get("/user-profiles/test_stage2_user")
    assert read_response.status_code == 200
    read_profile = read_response.json()["profile"]
    assert read_profile["city"] == "Suzhou"
    assert read_profile["price_band_preference"] == "premium"


def test_vector_index_status_endpoint_returns_status():
    response = client.get("/vector-index/status")

    assert response.status_code == 200
    payload = response.json()["status"]
    assert "backend" in payload
    assert "ready" in payload
    assert "load_source" in payload


def test_analytics_summary_accumulates_search_events():
    client.get("/multi-agent-task", params={"q": "通勤降噪耳机"})
    client.get("/multi-agent-task", params={"q": "拍照手机 预算5000"})

    response = client.get("/analytics/summary")

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["total_requests"] == 2
    assert summary["text_requests"] == 2
    assert summary["image_requests"] == 0
    assert summary["top_categories"]
    assert summary["top_products"]


def test_analytics_events_capture_image_request():
    client.post(
        "/multi-agent-task/image",
        files={"file": ("not-an-image.txt", b"not an image", "text/plain")},
    )

    response = client.get("/analytics/events", params={"limit": 1})

    assert response.status_code == 200
    event = response.json()["events"][0]
    assert event["image_search"] is True
    assert event["result_count"] > 0
    assert event["vector_backend"] is not None


def test_feedback_event_updates_analytics_summary():
    search_response = client.get("/multi-agent-task", params={"q": "通勤降噪耳机"})
    top_result = search_response.json()["results"][0]

    feedback_response = client.post(
        "/analytics/feedback",
        json={
            "event_type": "click",
            "product_id": top_result["id"],
            "product_name": top_result["name"],
            "query": "通勤降噪耳机",
            "user_id": "demo_student",
        },
    )

    assert feedback_response.status_code == 200
    summary = feedback_response.json()["summary"]
    assert summary["feedback_counts"]["click"] == 1
    assert summary["feedback_rates"]["click_rate"] == 1.0
    assert summary["top_feedback_products"][0]["name"] == "Sony WH-1000XM5"


def test_feedback_endpoint_rejects_unknown_event_type():
    response = client.post(
        "/analytics/feedback",
        json={
            "event_type": "share",
            "product_id": 1,
        },
    )

    assert response.status_code == 400


def test_analytics_dashboard_aggregates_query_and_product_performance():
    client.get("/multi-agent-task", params={"q": "通勤降噪耳机"})
    client.post(
        "/analytics/feedback",
        json={
            "event_type": "click",
            "product_id": 9,
            "product_name": "Sony WH-1000XM5",
            "query": "通勤降噪耳机",
        },
    )
    client.post(
        "/analytics/feedback",
        json={
            "event_type": "purchase",
            "product_id": 9,
            "product_name": "Sony WH-1000XM5",
            "query": "通勤降噪耳机",
        },
    )

    response = client.get("/analytics/dashboard", params={"limit": 5})

    assert response.status_code == 200
    dashboard = response.json()["dashboard"]
    assert dashboard["funnel"]["requests"] == 1
    assert dashboard["funnel"]["clicks"] == 1
    assert dashboard["funnel"]["purchases"] == 1
    assert dashboard["query_performance"][0]["query"] == "通勤降噪耳机"
    assert dashboard["query_performance"][0]["purchase_count"] == 1
    assert dashboard["product_performance"][0]["product_name"] == "Sony WH-1000XM5"
    assert dashboard["product_performance"][0]["click_count"] == 1
    assert dashboard["recent_feedback"]
    assert dashboard["recent_searches"]


def test_analytics_evaluation_returns_summary_and_cases():
    response = client.get("/analytics/evaluation")

    assert response.status_code == 200
    evaluation = response.json()["evaluation"]
    assert evaluation["summary"]["total_cases"] >= 10
    assert evaluation["summary"]["category_hit_rate"] >= 0.8
    assert evaluation["summary"]["top1_hit_rate"] >= 0.8
    assert evaluation["cases"]
    assert any(case["case_id"] == "commute_noise_canceling_headphones" for case in evaluation["cases"])
    assert any(case["case_id"] == "student_profile_value_laptop" for case in evaluation["cases"])


def test_products_endpoint_returns_catalog():
    response = client.get("/products")

    assert response.status_code == 200
    payload = response.json()
    assert "products" in payload
    assert len(payload["products"]) >= 12


def test_create_product_returns_vector_sync_status():
    response = client.post(
        "/products",
        json={
            "name": "QA Demo Headphones",
            "description": "用于测试的降噪耳机",
            "category": "耳机",
            "subcategory": "头戴耳机",
            "brand": "Sony",
            "price": 1999,
            "rating": 4.6,
            "tags": ["降噪", "测试"],
            "feature_highlights": ["长续航", "舒适佩戴"],
            "use_cases": ["通勤", "差旅"],
            "target_users": ["上班族", "学生"],
            "monthly_sales": 99,
            "promotion_tag": "测试活动",
            "inventory_total": 20,
            "warehouses": [{"name": "华东仓", "stock": 20}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"]["name"] == "QA Demo Headphones"
    assert payload["product"]["use_cases"] == ["通勤", "差旅"]
    assert payload["product"]["target_users"] == ["上班族", "学生"]
    assert "vector_status" in payload
