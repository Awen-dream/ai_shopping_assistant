from .runtime import reset_runtime_state
from ..domains.catalog import create_product, delete_product, list_products, upsert_product
from ..domains.vector_index import sync_vector_store_after_product_change


class CatalogApplicationService:
    """Owns product catalog write flows and their side effects."""

    def list_products(self):
        return list_products()

    def create_product(self, payload: dict):
        product = create_product(payload)
        sync_status = sync_vector_store_after_product_change(list_products())
        reset_runtime_state()
        return {"product": product, "vector_status": sync_status}

    def update_product(self, product_id: int, payload: dict):
        product = upsert_product(product_id, payload)
        sync_status = sync_vector_store_after_product_change(list_products())
        reset_runtime_state()
        return {"product": product, "vector_status": sync_status}

    def delete_product(self, product_id: int):
        deleted = delete_product(product_id)
        sync_status = sync_vector_store_after_product_change(list_products())
        reset_runtime_state()
        return {"product": deleted, "vector_status": sync_status}
