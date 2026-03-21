import os
from functools import lru_cache
from pathlib import Path

import yaml

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


SETTINGS_PATH = Path(__file__).resolve().parents[3] / "config" / "settings.yaml"


def load_settings(config_path: str | None = None) -> dict:
    path = Path(config_path) if config_path else SETTINGS_PATH
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_openai_key(config_path: str | None = None) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    settings = load_settings(config_path)
    return settings.get("openai_api_key") or None


def get_llm_model(default: str = "gpt-4o-mini") -> str:
    return load_settings().get("llm_model", default)


def get_embedding_model(default: str = "all-MiniLM-L6-v2") -> str:
    return load_settings().get("embedding_model", default)


def is_vector_search_enabled(default: bool = False) -> bool:
    raw_value = load_settings().get("enable_vector_search", default)
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def get_vector_store_backend(default: str = "local_faiss") -> str:
    return str(load_settings().get("vector_store_backend", default)).strip().lower()


def get_vector_index_strategy(default: str = "prefer_persisted") -> str:
    return str(load_settings().get("vector_index_strategy", default)).strip().lower()


def is_vector_auto_build_enabled(default: bool = True) -> bool:
    raw_value = load_settings().get("vector_auto_build", default)
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def get_vector_sync_on_product_change(default: str = "persisted") -> str:
    return str(load_settings().get("vector_sync_on_product_change", default)).strip().lower()


@lru_cache(maxsize=1)
def get_llm_client():
    api_key = load_openai_key()
    if not api_key or OpenAI is None:
        return None

    return OpenAI(api_key=api_key)


if __name__ == "__main__":
    client = get_llm_client()
    if client is None:
        print("OpenAI client unavailable: set OPENAI_API_KEY or config/settings.yaml.")
    else:
        prompt = "给我推荐三款性价比高的耳机"
        resp = client.chat.completions.create(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        print(resp.choices[0].message.content)
