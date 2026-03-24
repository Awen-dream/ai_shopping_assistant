from copy import deepcopy

from ...services.product_service import (
    list_products as list_products_store,
    read_products,
    refresh_products_cache,
    write_products,
)
from .model import normalize_product


def list_products():
    return list_products_store()


def get_product_by_id(product_id: int):
    for product in list_products_store():
        if product["id"] == product_id:
            return product
    return None


def create_product(payload: dict) -> dict:
    products = list_products_store().copy()
    next_id = max((product["id"] for product in products), default=0) + 1
    normalized = normalize_product(next_id, payload)
    products.append(normalized)
    write_products(products)
    refresh_products_cache()
    return normalized


def upsert_product(product_id: int, payload: dict) -> dict:
    products = read_products()
    for index, product in enumerate(products):
        if product["id"] == product_id:
            merged = deepcopy(product)
            merged.update(payload or {})
            normalized = normalize_product(product_id, merged)
            products[index] = normalized
            write_products(products)
            refresh_products_cache()
            return normalized

    normalized = normalize_product(product_id, payload)
    products.append(normalized)
    write_products(products)
    refresh_products_cache()
    return normalized


def delete_product(product_id: int) -> dict | None:
    products = read_products()
    for index, product in enumerate(products):
        if product["id"] == product_id:
            deleted = products.pop(index)
            write_products(products)
            refresh_products_cache()
            return deleted
    return None
