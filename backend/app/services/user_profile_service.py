import json
from functools import lru_cache

from app.services.product_service import get_user_profiles_path


def read_profiles() -> dict:
    path = get_user_profiles_path()
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f) or {}


def write_profiles(profiles: dict):
    path = get_user_profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


@lru_cache(maxsize=1)
def list_user_profiles():
    return read_profiles()


def refresh_user_profiles_cache():
    list_user_profiles.cache_clear()


def get_user_profile(user_id: str) -> dict | None:
    from app.domains.profiles.service import get_user_profile as domain_get_user_profile

    return domain_get_user_profile(user_id)


def upsert_user_profile(user_id: str, payload: dict) -> dict:
    from app.domains.profiles.service import upsert_user_profile as domain_upsert_user_profile

    return domain_upsert_user_profile(user_id, payload)


def merge_profiles(base_profile: dict | None, query_profile: dict | None) -> dict:
    from app.domains.profiles.model import merge_profiles as domain_merge_profiles

    return domain_merge_profiles(base_profile, query_profile)
