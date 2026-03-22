import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
PRODUCTS_PATH = DATA_DIR / "sample_products.json"
USER_PROFILES_PATH = DATA_DIR / "user_profiles.json"
FAISS_INDEX_PATH = DATA_DIR / "product_index.faiss"

DEFAULT_PRODUCT = {
    "name": "",
    "description": "",
    "category": "",
    "subcategory": "",
    "brand": "",
    "price": 0,
    "rating": 0,
    "tags": [],
    "monthly_sales": 0,
    "promotion_tag": "",
    "inventory_total": 0,
    "warehouses": [],
}


def get_products_path() -> Path:
    return PRODUCTS_PATH


def get_product_index_path() -> Path:
    return FAISS_INDEX_PATH


def get_user_profiles_path() -> Path:
    return USER_PROFILES_PATH


@lru_cache(maxsize=1)
def list_products():
    with PRODUCTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def refresh_products_cache():
    list_products.cache_clear()


def _write_products(products: list[dict]):
    PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PRODUCTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def _normalize_product(product_id: int, payload: dict | None) -> dict:
    normalized = deepcopy(DEFAULT_PRODUCT)
    if payload:
        normalized.update(payload)

    tags = normalized.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    warehouses = normalized.get("warehouses") or []
    normalized_warehouses = []
    for warehouse in warehouses:
        if not isinstance(warehouse, dict):
            continue
        normalized_warehouses.append({
            "name": warehouse.get("name", ""),
            "stock": int(warehouse.get("stock", 0)),
        })

    normalized["id"] = int(product_id)
    normalized["name"] = normalized.get("name", "")
    normalized["description"] = normalized.get("description", "")
    normalized["category"] = normalized.get("category", "")
    normalized["subcategory"] = normalized.get("subcategory", "")
    normalized["brand"] = normalized.get("brand", "")
    normalized["price"] = float(normalized.get("price", 0))
    normalized["rating"] = float(normalized.get("rating", 0))
    normalized["tags"] = tags
    normalized["monthly_sales"] = int(normalized.get("monthly_sales", 0))
    normalized["promotion_tag"] = normalized.get("promotion_tag", "")
    normalized["inventory_total"] = int(normalized.get("inventory_total", 0))
    if not normalized_warehouses and normalized["inventory_total"] > 0:
        normalized_warehouses = [{"name": "默认仓", "stock": normalized["inventory_total"]}]
    if normalized["inventory_total"] <= 0 and normalized_warehouses:
        normalized["inventory_total"] = sum(warehouse["stock"] for warehouse in normalized_warehouses)
    normalized["warehouses"] = normalized_warehouses
    return normalized


def get_product_by_id(product_id: int):
    for product in list_products():
        if product["id"] == product_id:
            return product
    return None


def create_product(payload: dict) -> dict:
    products = list_products().copy()
    next_id = max((product["id"] for product in products), default=0) + 1
    normalized = _normalize_product(next_id, payload)
    products.append(normalized)
    _write_products(products)
    refresh_products_cache()
    return normalized


def upsert_product(product_id: int, payload: dict) -> dict:
    products = list_products().copy()
    for index, product in enumerate(products):
        if product["id"] == product_id:
            merged = deepcopy(product)
            merged.update(payload or {})
            normalized = _normalize_product(product_id, merged)
            products[index] = normalized
            _write_products(products)
            refresh_products_cache()
            return normalized

    normalized = _normalize_product(product_id, payload)
    products.append(normalized)
    _write_products(products)
    refresh_products_cache()
    return normalized


def delete_product(product_id: int) -> dict | None:
    products = list_products().copy()
    for index, product in enumerate(products):
        if product["id"] == product_id:
            deleted = products.pop(index)
            _write_products(products)
            refresh_products_cache()
            return deleted
    return None
