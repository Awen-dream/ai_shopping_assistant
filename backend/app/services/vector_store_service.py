import json
import hashlib
from pathlib import Path
from typing import List

import numpy as np

from app.domains.vector_index.model import build_product_text as domain_build_product_text
from app.services.embedding_service import get_sentence_transformer
from app.services.llm_client import (
    get_embedding_model,
    get_vector_index_strategy,
    get_vector_store_backend,
    get_vector_sync_on_product_change,
    is_vector_auto_build_enabled,
    is_vector_search_enabled,
)
from app.services.product_service import get_product_index_path

try:
    import faiss
except ImportError:
    faiss = None


_RUNTIME_VECTOR_STORE_OVERRIDE = None


def build_product_text(product: dict) -> str:
    return domain_build_product_text(product)


def build_products_signature(products: List[dict]) -> str:
    hasher = hashlib.sha256()
    for product in products:
        hasher.update(str(product.get("id", "")).encode("utf-8"))
        hasher.update(b"|")
        hasher.update(build_product_text(product).encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


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
        self.load_source = "disabled"

    def search(self, query: str, topk: int = 20) -> list[tuple[dict, float]]:
        return []

    def status(self) -> dict:
        return {
            "backend": self.backend_name,
            "ready": self.ready,
            "load_source": self.load_source,
            "product_count": len(self.products),
            "persisted_index_exists": get_product_index_path().exists(),
            "persisted_metadata_exists": get_product_index_metadata_path().exists(),
        }


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
            self.load_source = "faiss_unavailable"
            return

        self.model = get_sentence_transformer()
        if self.model is None:
            self.load_source = "model_unavailable"
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
            self.load_source = "persisted_missing"
            return False

        try:
            with metadata_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)

            expected_ids = [product["id"] for product in self.products]
            if metadata.get("product_ids") != expected_ids:
                self.load_source = "persisted_metadata_mismatch"
                return False
            if metadata.get("product_content_signature") != build_products_signature(self.products):
                self.load_source = "persisted_content_mismatch"
                return False
            if metadata.get("embedding_model") != get_embedding_model():
                self.load_source = "persisted_model_mismatch"
                return False

            self.index = faiss.read_index(str(index_path))
            self.load_source = "persisted"
            return True
        except Exception:
            self.index = None
            self.load_source = "persisted_load_failed"
            return False

    def _rebuild_runtime_index(self, write_to_disk: bool = False) -> bool:
        try:
            texts = [build_product_text(product) for product in self.products]
            embeddings = self.model.encode(texts, normalize_embeddings=True).astype(np.float32)
            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            self.index = index
            self.load_source = "rebuilt_and_persisted" if write_to_disk else "rebuilt_runtime"
            if write_to_disk:
                self.persist()
            return True
        except Exception:
            self.index = None
            self.load_source = "rebuild_failed"
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
            "product_content_signature": build_products_signature(self.products),
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
            self.load_source = "model_unavailable"
            return

        self.ready = self._rebuild_runtime_index(write_to_disk=False)


def _same_products(products: List[dict], other_products: List[dict]) -> bool:
    return [product.get("id") for product in products] == [product.get("id") for product in other_products]


def set_runtime_vector_store_override(store: BaseVectorStore | None):
    global _RUNTIME_VECTOR_STORE_OVERRIDE
    _RUNTIME_VECTOR_STORE_OVERRIDE = store


def get_runtime_vector_store_override():
    return _RUNTIME_VECTOR_STORE_OVERRIDE


def delete_persisted_vector_store_artifacts():
    for path in [get_product_index_path(), get_product_index_metadata_path()]:
        if path.exists():
            path.unlink()


def create_vector_store(products: List[dict]) -> BaseVectorStore:
    runtime_override = get_runtime_vector_store_override()
    if runtime_override is not None and _same_products(products, runtime_override.products):
        return runtime_override

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


def rebuild_vector_store(products: List[dict], persist: bool = True) -> dict:
    if faiss is None:
        raise RuntimeError("faiss-cpu is not available in the current environment.")

    backend = get_vector_store_backend()
    if backend == "local_faiss":
        store = FaissVectorStore(products)
        if store.model is None:
            raise RuntimeError("Embedding model unavailable for local FAISS rebuild.")
        if not store._rebuild_runtime_index(write_to_disk=persist):
            raise RuntimeError("Failed to rebuild local FAISS index.")
        if persist:
            set_runtime_vector_store_override(None)
        else:
            set_runtime_vector_store_override(store)
        return store.status()

    if backend in {"memory", "runtime_faiss", "in_memory"}:
        store = MemoryFaissVectorStore(products)
        if not store.ready:
            raise RuntimeError("Failed to rebuild in-memory vector index.")
        set_runtime_vector_store_override(store)
        return store.status()

    if backend in {"disabled", "off", "none"}:
        set_runtime_vector_store_override(None)
        return DisabledVectorStore(products).status()

    raise RuntimeError(f"Vector rebuild is not implemented for backend '{backend}'.")


def sync_vector_store_after_product_change(products: List[dict]) -> dict:
    if not is_vector_search_enabled():
        set_runtime_vector_store_override(None)
        return DisabledVectorStore(products).status()

    strategy = get_vector_sync_on_product_change()
    if strategy in {"persist", "persisted", "disk"}:
        return rebuild_vector_store(products, persist=True)
    if strategy in {"runtime", "memory", "volatile"}:
        return rebuild_vector_store(products, persist=False)
    if strategy in {"invalidate", "clear"}:
        set_runtime_vector_store_override(None)
        delete_persisted_vector_store_artifacts()
        return {
            "backend": get_vector_store_backend(),
            "ready": False,
            "load_source": "invalidated",
            "product_count": len(products),
            "persisted_index_exists": False,
            "persisted_metadata_exists": False,
        }

    return rebuild_vector_store(products, persist=True)
