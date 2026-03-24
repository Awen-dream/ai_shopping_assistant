import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
PRODUCTS_PATH = DATA_DIR / "sample_products.json"
USER_PROFILES_PATH = DATA_DIR / "user_profiles.json"
FAISS_INDEX_PATH = DATA_DIR / "product_index.faiss"

def get_products_path() -> Path:
    return PRODUCTS_PATH


def get_product_index_path() -> Path:
    return FAISS_INDEX_PATH


def get_user_profiles_path() -> Path:
    return USER_PROFILES_PATH


@lru_cache(maxsize=1)
def list_products():
    return read_products()


def refresh_products_cache():
    list_products.cache_clear()


def write_products(products: list[dict]):
    PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PRODUCTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def read_products() -> list[dict]:
    with PRODUCTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_product_by_id(product_id: int):
    from app.domains.catalog.service import get_product_by_id as domain_get_product_by_id

    return domain_get_product_by_id(product_id)


def create_product(payload: dict) -> dict:
    from app.domains.catalog.service import create_product as domain_create_product

    return domain_create_product(payload)


def upsert_product(product_id: int, payload: dict) -> dict:
    from app.domains.catalog.service import upsert_product as domain_upsert_product

    return domain_upsert_product(product_id, payload)


def delete_product(product_id: int) -> dict | None:
    from app.domains.catalog.service import delete_product as domain_delete_product

    return domain_delete_product(product_id)
