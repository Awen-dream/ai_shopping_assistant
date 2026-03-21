import numpy as np

from app.services.llm_client import get_embedding_model
from app.services.product_service import get_product_index_path, list_products

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


def build_faiss_index():
    if faiss is None or SentenceTransformer is None:
        raise RuntimeError("faiss-cpu and sentence-transformers are required to build the index.")

    products = list_products()
    texts = [
        " ".join(
            [
                product.get("name", ""),
                product.get("description", ""),
                product.get("category", ""),
                product.get("brand", ""),
                " ".join(product.get("tags", [])),
            ]
        ).strip()
        for product in products
    ]

    model = SentenceTransformer(get_embedding_model(), local_files_only=True)
    vectors = model.encode(texts, normalize_embeddings=True).astype(np.float32)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    output_path = get_product_index_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_path))
    print(f"FAISS index built with {len(products)} products at {output_path}.")


if __name__ == "__main__":
    build_faiss_index()
