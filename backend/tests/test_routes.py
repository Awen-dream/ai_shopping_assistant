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


def test_user_profile_crud_roundtrip():
    save_response = client.put(
        "/user-profiles/test_stage2_user",
        json={
            "preferred_brand": ["Apple"],
            "budget_range": [1000, 9000],
            "interests": ["轻便"],
            "preferred_categories": ["手机", "耳机"],
            "city": "Suzhou",
        },
    )

    assert save_response.status_code == 200
    saved_profile = save_response.json()["profile"]
    assert saved_profile["preferred_brand"] == ["Apple"]

    read_response = client.get("/user-profiles/test_stage2_user")
    assert read_response.status_code == 200
    read_profile = read_response.json()["profile"]
    assert read_profile["city"] == "Suzhou"


def test_vector_index_status_endpoint_returns_status():
    response = client.get("/vector-index/status")

    assert response.status_code == 200
    payload = response.json()["status"]
    assert "backend" in payload
    assert "ready" in payload
    assert "load_source" in payload


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
            "monthly_sales": 99,
            "promotion_tag": "测试活动",
            "inventory_total": 20,
            "warehouses": [{"name": "华东仓", "stock": 20}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"]["name"] == "QA Demo Headphones"
    assert "vector_status" in payload
