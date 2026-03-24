from copy import deepcopy
from datetime import datetime, timezone

from ...services.user_profile_service import get_user_profile_repository, refresh_user_profiles_cache
from .model import normalize_profile


def get_user_profile(user_id: str) -> dict | None:
    profile = get_user_profile_repository().get_profile(user_id)
    if not profile:
        return None
    return normalize_profile(user_id, profile)


def upsert_user_profile(user_id: str, payload: dict) -> dict:
    repository = get_user_profile_repository()
    existing = repository.get_profile(user_id) or {}
    merged = deepcopy(existing)
    merged.update(payload or {})
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    normalized = normalize_profile(user_id, merged)
    repository.upsert_profile(user_id, normalized)
    refresh_user_profiles_cache()
    return normalized
