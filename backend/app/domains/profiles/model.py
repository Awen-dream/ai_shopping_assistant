from copy import deepcopy
from datetime import datetime, timezone


DEFAULT_USER_PROFILE = {
    "preferred_brand": [],
    "budget_range": [0, 15000],
    "interests": [],
    "category": "",
    "preferred_categories": [],
    "price_sensitivity": "medium",
    "scenario": "",
    "sort_preference": "balanced",
    "urgency": "normal",
    "fulfillment_preference": "standard",
    "required_features": [],
    "city": "",
}


def _normalize_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if item]


def normalize_profile(user_id: str, payload: dict | None) -> dict:
    normalized = deepcopy(DEFAULT_USER_PROFILE)
    if payload:
        normalized.update(payload)

    budget_range = normalized.get("budget_range") or DEFAULT_USER_PROFILE["budget_range"][:]
    if not isinstance(budget_range, list) or len(budget_range) != 2:
        budget_range = DEFAULT_USER_PROFILE["budget_range"][:]

    normalized["user_id"] = user_id
    normalized["preferred_brand"] = _normalize_list(normalized.get("preferred_brand"))
    normalized["budget_range"] = [int(budget_range[0]), int(budget_range[1])]
    normalized["interests"] = _normalize_list(normalized.get("interests"))
    normalized["preferred_categories"] = _normalize_list(normalized.get("preferred_categories"))
    normalized["category"] = normalized.get("category") or ""
    normalized["price_sensitivity"] = normalized.get("price_sensitivity") or "medium"
    normalized["scenario"] = normalized.get("scenario") or ""
    normalized["sort_preference"] = normalized.get("sort_preference") or "balanced"
    normalized["urgency"] = normalized.get("urgency") or "normal"
    normalized["fulfillment_preference"] = normalized.get("fulfillment_preference") or "standard"
    normalized["required_features"] = _normalize_list(normalized.get("required_features"))
    normalized["city"] = normalized.get("city") or ""
    normalized["updated_at"] = normalized.get("updated_at") or datetime.now(timezone.utc).isoformat()
    return normalized


def merge_profiles(base_profile: dict | None, query_profile: dict | None) -> dict:
    merged = deepcopy(DEFAULT_USER_PROFILE)
    if base_profile:
        merged.update(base_profile)
    if query_profile:
        merged.update(query_profile)

    merged["preferred_brand"] = list(
        dict.fromkeys((base_profile or {}).get("preferred_brand", []) + (query_profile or {}).get("preferred_brand", []))
    )
    merged["interests"] = list(
        dict.fromkeys((base_profile or {}).get("interests", []) + (query_profile or {}).get("interests", []))
    )
    merged["preferred_categories"] = list(
        dict.fromkeys(
            (base_profile or {}).get("preferred_categories", []) + (query_profile or {}).get("preferred_categories", [])
        )
    )
    merged["required_features"] = list(
        dict.fromkeys(
            (base_profile or {}).get("required_features", []) + (query_profile or {}).get("required_features", [])
        )
    )

    query_budget = (query_profile or {}).get("budget_range")
    merged["budget_range"] = query_budget if query_budget else (base_profile or {}).get(
        "budget_range",
        DEFAULT_USER_PROFILE["budget_range"][:],
    )
    merged["category"] = (query_profile or {}).get("category") or (base_profile or {}).get("category", "")
    merged["price_sensitivity"] = (query_profile or {}).get("price_sensitivity") or (
        base_profile or {}
    ).get("price_sensitivity", "medium")
    merged["scenario"] = (query_profile or {}).get("scenario") or (base_profile or {}).get("scenario", "")
    merged["sort_preference"] = (query_profile or {}).get("sort_preference") or (
        base_profile or {}
    ).get("sort_preference", "balanced")
    merged["urgency"] = (query_profile or {}).get("urgency") or (base_profile or {}).get("urgency", "normal")
    merged["fulfillment_preference"] = (query_profile or {}).get("fulfillment_preference") or (
        base_profile or {}
    ).get("fulfillment_preference", "standard")
    merged["city"] = (base_profile or {}).get("city") or ""
    return merged
