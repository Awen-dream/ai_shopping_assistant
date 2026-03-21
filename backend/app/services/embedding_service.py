from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.services.llm_client import get_embedding_model


@lru_cache(maxsize=1)
def get_sentence_transformer():
    if SentenceTransformer is None:
        return None

    model_name = get_embedding_model()
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return None
