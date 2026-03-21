from app.services.product_service import list_products
from app.services.vector_store_service import FaissVectorStore


def build_faiss_index():
    products = list_products()
    store = FaissVectorStore(products)
    if store.model is None:
        raise RuntimeError("sentence-transformers model unavailable for local FAISS build.")
    if not store.ready:
        if not store._rebuild_runtime_index(write_to_disk=True):
            raise RuntimeError("Failed to build local FAISS index.")
    else:
        store.persist()

    print(f"FAISS index built for {len(products)} products.")


if __name__ == "__main__":
    build_faiss_index()
