import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.services.product_service import DATA_DIR


ANALYTICS_EVENTS_PATH = DATA_DIR / "recommendation_events.jsonl"
ANALYTICS_FEEDBACK_PATH = DATA_DIR / "recommendation_feedback.jsonl"


def get_analytics_events_path() -> Path:
    return ANALYTICS_EVENTS_PATH


def get_analytics_feedback_path() -> Path:
    return ANALYTICS_FEEDBACK_PATH


def build_recommendation_event(
    results: list[dict],
    query: str = "",
    user_id: str | None = None,
    image_search: bool = False,
    vector_status: dict | None = None,
) -> dict:
    top_result = results[0] if results else {}
    best_offer = top_result.get("best_offer") or {}
    return {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "user_id": user_id,
        "image_search": image_search,
        "result_count": len(results),
        "top_product_id": top_result.get("id"),
        "top_product_name": top_result.get("name"),
        "top_category": top_result.get("category"),
        "top_match_score": top_result.get("match_score"),
        "top_reason": top_result.get("reason"),
        "best_store": best_offer.get("store"),
        "best_channel": best_offer.get("channel"),
        "best_price": best_offer.get("sale_price"),
        "best_fulfillment_type": best_offer.get("fulfillment_type"),
        "best_fulfillment_warehouse": best_offer.get("fulfillment_warehouse"),
        "vector_backend": (vector_status or {}).get("backend"),
        "vector_ready": (vector_status or {}).get("ready"),
        "vector_source": (vector_status or {}).get("load_source"),
    }


def log_recommendation_event(event: dict):
    path = get_analytics_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def build_feedback_event(
    event_type: str,
    product_id: int,
    product_name: str = "",
    query: str = "",
    user_id: str | None = None,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "product_id": product_id,
        "product_name": product_name,
        "query": query,
        "user_id": user_id,
    }


def log_feedback_event(event: dict):
    path = get_analytics_feedback_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def list_recommendation_events(limit: int = 20) -> list[dict]:
    path = get_analytics_events_path()
    if not path.exists():
        return []

    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if limit <= 0:
        return events
    return events[-limit:][::-1]


def list_feedback_events(limit: int = 20) -> list[dict]:
    path = get_analytics_feedback_path()
    if not path.exists():
        return []

    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if limit <= 0:
        return events
    return events[-limit:][::-1]


def _top_counter_items(counter: Counter, limit: int = 5) -> list[dict]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def get_analytics_summary() -> dict:
    events = list_recommendation_events(limit=0)
    feedback_events = list_feedback_events(limit=0)
    if not events and not feedback_events:
        return {
            "total_requests": 0,
            "text_requests": 0,
            "image_requests": 0,
            "average_result_count": 0.0,
            "feedback_counts": {"click": 0, "favorite": 0, "purchase": 0},
            "feedback_rates": {"click_rate": 0.0, "favorite_rate": 0.0, "purchase_rate": 0.0},
            "top_queries": [],
            "top_categories": [],
            "top_products": [],
            "top_stores": [],
            "top_feedback_products": [],
            "last_event_at": None,
        }

    query_counter = Counter(event["query"] for event in events if event.get("query"))
    category_counter = Counter(event["top_category"] for event in events if event.get("top_category"))
    product_counter = Counter(event["top_product_name"] for event in events if event.get("top_product_name"))
    store_counter = Counter(event["best_store"] for event in events if event.get("best_store"))
    image_requests = sum(1 for event in events if event.get("image_search"))
    text_requests = len(events) - image_requests
    average_result_count = round(
        sum(event.get("result_count", 0) for event in events) / max(len(events), 1),
        2,
    )
    feedback_counter = Counter(event["event_type"] for event in feedback_events if event.get("event_type"))
    feedback_product_counter = Counter(event["product_name"] for event in feedback_events if event.get("product_name"))
    request_count = max(len(events), 1)
    click_count = feedback_counter.get("click", 0)
    favorite_count = feedback_counter.get("favorite", 0)
    purchase_count = feedback_counter.get("purchase", 0)
    last_candidates = [event.get("timestamp") for event in [*events, *feedback_events] if event.get("timestamp")]

    return {
        "total_requests": len(events),
        "text_requests": text_requests,
        "image_requests": image_requests,
        "average_result_count": average_result_count,
        "feedback_counts": {
            "click": click_count,
            "favorite": favorite_count,
            "purchase": purchase_count,
        },
        "feedback_rates": {
            "click_rate": round(click_count / request_count, 2),
            "favorite_rate": round(favorite_count / request_count, 2),
            "purchase_rate": round(purchase_count / request_count, 2),
        },
        "top_queries": _top_counter_items(query_counter),
        "top_categories": _top_counter_items(category_counter),
        "top_products": _top_counter_items(product_counter),
        "top_stores": _top_counter_items(store_counter),
        "top_feedback_products": _top_counter_items(feedback_product_counter),
        "last_event_at": max(last_candidates) if last_candidates else None,
    }
