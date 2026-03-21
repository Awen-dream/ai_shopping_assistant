import json
from pathlib import Path
from typing import List

import numpy as np

from app.services.embedding_service import get_sentence_transformer
from app.services.llm_client import (
    get_embedding_model,
    get_vector_index_strategy,
    get_vector_store_backend,
    is_vector_auto_build_enabled,
    is_vector_search_enabled,
)
from app.services.product_service import get_product_index_path

try:
    import faiss
except ImportError:
    faiss = None


def build_product_text(product: dict) -> str:
    fields = [
        product.get("name", ""),
        product.get("description", ""),
        product.get("category", ""),
        product.get("subcategory", ""),
        product.get("brand", ""),
        " ".join(product.get("tags", [])),
        product.get("promotion_tag", ""),
    ]
    return " ".join(part for part in fields if part)


def get_product_index_metadata_path() -> Path:
    index_path = get_product_index_path()
    return index_path.with_suffix(".meta.json")


class BaseVectorStore:
    backend_name = "disabled"

    def __init__(self, products: List[dict]):
        self.products = products
        self.model = None
        self.index = None
        self.ready = False

    def search(self, query: str, topk: int = 20) -> list[tuple[dict, float]]:
        return []


class DisabledVectorStore(BaseVectorStore):
    backend_name = "disabled"


class MilvusVectorStore(BaseVectorStore):
    backend_name = "milvus"

    # Placeholder for future stage-2/3 integration.
    pass


class BaseFaissVectorStore(BaseVectorStore):
    def __init__(self, products: List[dict]):
        super().__init__(products)
        if faiss is None:
            return

        self.model = get_sentence_transformer()
        if self.model is None:
            return

        strategy = get_vector_index_strategy()
        if strategy == "persisted_only":
            self.ready = self._load_persisted_index()
        elif strategy == "rebuild":
            self.ready = self._rebuild_runtime_index()
        else:
            self.ready = self._load_persisted_index()
            if not self.ready and is_vector_auto_build_enabled():
                self.ready = self._rebuild_runtime_index(write_to_disk=True)

    def _load_persisted_index(self) -> bool:
        index_path = get_product_index_path()
        metadata_path = get_product_index_metadata_path()
        if not index_path.exists() or not metadata_path.exists():
            return False

        try:
            with metadata_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)

            expected_ids = [product["id"] for product in self.products]
            if metadata.get("product_ids") != expected_ids:
                return False
            if metadata.get("embedding_model") != get_embedding_model():
                return False

            self.index = faiss.read_index(str(index_path))
            return True
        except Exception:
            self.index = None
            return False

    def _rebuild_runtime_index(self, write_to_disk: bool = False) -> bool:
        try:
            texts = [build_product_text(product) for product in self.products]
            embeddings = self.model.encode(texts, normalize_embeddings=True).astype(np.float32)
            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            self.index = index
            if write_to_disk:
                self.persist()
            return True
        except Exception:
            self.index = None
            return False

    def persist(self):
        if self.index is None or faiss is None:
            return

        index_path = get_product_index_path()
        metadata_path = get_product_index_metadata_path()
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_path))

        metadata = {
            "embedding_model": get_embedding_model(),
            "product_ids": [product["id"] for product in self.products],
            "product_count": len(self.products),
            "backend": self.backend_name,
        }
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def search(self, query: str, topk: int = 20) -> list[tuple[dict, float]]:
        if not self.ready or self.index is None or self.model is None:
            return []

        query_embedding = self.model.encode([query], normalize_embeddings=True).astype(np.float32)
        scores, indices = self.index.search(query_embedding, min(topk, len(self.products)))
        return [
            (self.products[index], float(scores[0][position]))
            for position, index in enumerate(indices[0])
            if 0 <= index < len(self.products)
        ]


class FaissVectorStore(BaseFaissVectorStore):
    backend_name = "local_faiss"


class MemoryFaissVectorStore(BaseFaissVectorStore):
    backend_name = "memory"

    def __init__(self, products: List[dict]):
        BaseVectorStore.__init__(self, products)
        if faiss is None:
            return

        self.model = get_sentence_transformer()
        if self.model is None:
            return

        self.ready = self._rebuild_runtime_index(write_to_disk=False)


def create_vector_store(products: List[dict]) -> BaseVectorStore:
    if not is_vector_search_enabled():
        return DisabledVectorStore(products)

    backend = get_vector_store_backend()
    if backend == "local_faiss":
        return FaissVectorStore(products)
    if backend in {"memory", "runtime_faiss", "in_memory"}:
        return MemoryFaissVectorStore(products)
    if backend == "milvus":
        return MilvusVectorStore(products)
    if backend in {"disabled", "off", "none"}:
        return DisabledVectorStore(products)

    # Unknown backend falls back safely for local development.
    return DisabledVectorStore(products)
