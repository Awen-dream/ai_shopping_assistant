import json
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache

from app.services.product_service import get_user_profiles_path


DEFAULT_USER_PROFILE = {
    "preferred_brand": [],
    "budget_range": [0, 15000],
    "interests": [],
    "category": "",
    "preferred_categories": [],
    "price_sensitivity": "medium",
    "city": "",
}


def _read_profiles() -> dict:
    path = get_user_profiles_path()
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f) or {}


def _write_profiles(profiles: dict):
    path = get_user_profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def _normalize_profile(user_id: str, payload: dict | None) -> dict:
    normalized = deepcopy(DEFAULT_USER_PROFILE)
    if payload:
        normalized.update(payload)

    preferred_brand = normalized.get("preferred_brand") or []
    if isinstance(preferred_brand, str):
        preferred_brand = [preferred_brand]

    interests = normalized.get("interests") or []
    if isinstance(interests, str):
        interests = [interests]

    preferred_categories = normalized.get("preferred_categories") or []
    if isinstance(preferred_categories, str):
        preferred_categories = [preferred_categories]

    budget_range = normalized.get("budget_range") or DEFAULT_USER_PROFILE["budget_range"][:]
    if not isinstance(budget_range, list) or len(budget_range) != 2:
        budget_range = DEFAULT_USER_PROFILE["budget_range"][:]

    normalized["user_id"] = user_id
    normalized["preferred_brand"] = preferred_brand
    normalized["budget_range"] = [int(budget_range[0]), int(budget_range[1])]
    normalized["interests"] = interests
    normalized["preferred_categories"] = preferred_categories
    normalized["category"] = normalized.get("category") or ""
    normalized["price_sensitivity"] = normalized.get("price_sensitivity") or "medium"
    normalized["city"] = normalized.get("city") or ""
    normalized["updated_at"] = normalized.get("updated_at") or datetime.now(timezone.utc).isoformat()
    return normalized


@lru_cache(maxsize=1)
def list_user_profiles():
    return _read_profiles()


def refresh_user_profiles_cache():
    list_user_profiles.cache_clear()


def get_user_profile(user_id: str) -> dict | None:
    profiles = list_user_profiles()
    profile = profiles.get(user_id)
    if not profile:
        return None
    return _normalize_profile(user_id, profile)


def upsert_user_profile(user_id: str, payload: dict) -> dict:
    profiles = _read_profiles()
    existing = profiles.get(user_id, {})
    merged = deepcopy(existing)
    merged.update(payload or {})
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    normalized = _normalize_profile(user_id, merged)
    profiles[user_id] = normalized
    _write_profiles(profiles)
    refresh_user_profiles_cache()
    return normalized


def merge_profiles(base_profile: dict | None, query_profile: dict | None) -> dict:
    merged = deepcopy(DEFAULT_USER_PROFILE)
    if base_profile:
        merged.update(base_profile)
    if query_profile:
        merged.update(query_profile)

    merged["preferred_brand"] = list(dict.fromkeys(
        (base_profile or {}).get("preferred_brand", []) + (query_profile or {}).get("preferred_brand", [])
    ))
    merged["interests"] = list(dict.fromkeys(
        (base_profile or {}).get("interests", []) + (query_profile or {}).get("interests", [])
    ))
    merged["preferred_categories"] = list(dict.fromkeys(
        (base_profile or {}).get("preferred_categories", []) + (query_profile or {}).get("preferred_categories", [])
    ))

    query_budget = (query_profile or {}).get("budget_range")
    merged["budget_range"] = query_budget if query_budget else (base_profile or {}).get(
        "budget_range",
        DEFAULT_USER_PROFILE["budget_range"][:],
    )
    merged["category"] = (query_profile or {}).get("category") or (base_profile or {}).get("category", "")
    merged["price_sensitivity"] = (query_profile or {}).get("price_sensitivity") or (
        base_profile or {}
    ).get("price_sensitivity", "medium")
    merged["city"] = (base_profile or {}).get("city") or ""
    return merged
