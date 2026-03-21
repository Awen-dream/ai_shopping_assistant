import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
PRODUCTS_PATH = DATA_DIR / "sample_products.json"
FAISS_INDEX_PATH = DATA_DIR / "product_index.faiss"


def get_products_path() -> Path:
    return PRODUCTS_PATH


def get_product_index_path() -> Path:
    return FAISS_INDEX_PATH


@lru_cache(maxsize=1)
def list_products():
    with PRODUCTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def refresh_products_cache():
    list_products.cache_clear()


def get_product_by_id(product_id: int):
    for product in list_products():
        if product["id"] == product_id:
            return product
    return None
