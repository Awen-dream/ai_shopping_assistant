from ...services.vector_store_service import (
    create_vector_store as create_vector_store_infra,
    get_product_index_metadata_path,
    rebuild_vector_store as rebuild_vector_store_infra,
    set_runtime_vector_store_override,
    sync_vector_store_after_product_change as sync_vector_store_after_product_change_infra,
)
from .model import build_product_text


def create_vector_store(products):
    return create_vector_store_infra(products)


def rebuild_vector_store(products, persist: bool = True):
    return rebuild_vector_store_infra(products, persist=persist)


def sync_vector_store_after_product_change(products):
    return sync_vector_store_after_product_change_infra(products)
