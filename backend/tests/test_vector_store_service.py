from app.services import vector_store_service


def test_create_vector_store_returns_disabled_when_switch_off(monkeypatch):
    monkeypatch.setattr(vector_store_service, "is_vector_search_enabled", lambda: False)

    store = vector_store_service.create_vector_store([])

    assert store.backend_name == "disabled"


def test_create_vector_store_supports_memory_backend(monkeypatch):
    monkeypatch.setattr(vector_store_service, "is_vector_search_enabled", lambda: True)
    monkeypatch.setattr(vector_store_service, "get_vector_store_backend", lambda: "memory")

    class DummyMemoryStore:
        backend_name = "memory"

        def __init__(self, products):
            self.products = products

    monkeypatch.setattr(vector_store_service, "MemoryFaissVectorStore", DummyMemoryStore)

    store = vector_store_service.create_vector_store([{"id": 1}])

    assert store.backend_name == "memory"
    assert store.products == [{"id": 1}]


def test_build_product_text_includes_stage2_fields():
    text = vector_store_service.build_product_text(
        {
            "name": "MacBook Air M3",
            "description": "light laptop",
            "category": "笔记本",
            "subcategory": "轻薄本",
            "brand": "Apple",
            "tags": ["轻薄", "办公"],
            "feature_highlights": ["长续航", "静音设计"],
            "use_cases": ["学习", "差旅"],
            "target_users": ["学生", "内容创作者"],
            "promotion_tag": "教育优惠",
        }
    )

    assert "轻薄本" in text
    assert "教育优惠" in text
    assert "差旅" in text
    assert "内容创作者" in text


def test_build_products_signature_changes_when_product_text_changes():
    products = [
        {
            "id": 1,
            "name": "MacBook Air M3",
            "description": "light laptop",
            "category": "笔记本",
            "tags": ["轻薄"],
        }
    ]

    original_signature = vector_store_service.build_products_signature(products)
    changed_signature = vector_store_service.build_products_signature(
        [
            {
                "id": 1,
                "name": "MacBook Air M3",
                "description": "light laptop with OLED",
                "category": "笔记本",
                "tags": ["轻薄"],
            }
        ]
    )

    assert original_signature != changed_signature
