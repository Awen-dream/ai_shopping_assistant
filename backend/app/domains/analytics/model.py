from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4


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


def top_counter_items(counter: Counter, limit: int = 5) -> list[dict]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def build_query_performance(events: list[dict], feedback_events: list[dict], limit: int = 5) -> list[dict]:
    performance = {}
    for event in events:
        query = event.get("query")
        if not query:
            continue
        record = performance.setdefault(
            query,
            {"query": query, "request_count": 0, "click_count": 0, "favorite_count": 0, "purchase_count": 0},
        )
        record["request_count"] += 1

    for feedback_event in feedback_events:
        query = feedback_event.get("query")
        if not query or query not in performance:
            continue
        event_type = feedback_event.get("event_type")
        if event_type == "click":
            performance[query]["click_count"] += 1
        elif event_type == "favorite":
            performance[query]["favorite_count"] += 1
        elif event_type == "purchase":
            performance[query]["purchase_count"] += 1

    items = []
    for _, record in performance.items():
        request_count = max(record["request_count"], 1)
        record["click_rate"] = round(record["click_count"] / request_count, 2)
        record["purchase_rate"] = round(record["purchase_count"] / request_count, 2)
        items.append(record)

    return sorted(items, key=lambda item: (item["request_count"], item["click_count"], item["purchase_count"]), reverse=True)[
        :limit
    ]


def build_product_performance(events: list[dict], feedback_events: list[dict], limit: int = 5) -> list[dict]:
    performance = {}
    for event in events:
        product_name = event.get("top_product_name")
        if not product_name:
            continue
        record = performance.setdefault(
            product_name,
            {
                "product_name": product_name,
                "recommend_count": 0,
                "click_count": 0,
                "favorite_count": 0,
                "purchase_count": 0,
            },
        )
        record["recommend_count"] += 1

    for feedback_event in feedback_events:
        product_name = feedback_event.get("product_name")
        if not product_name:
            continue
        record = performance.setdefault(
            product_name,
            {
                "product_name": product_name,
                "recommend_count": 0,
                "click_count": 0,
                "favorite_count": 0,
                "purchase_count": 0,
            },
        )
        event_type = feedback_event.get("event_type")
        if event_type == "click":
            record["click_count"] += 1
        elif event_type == "favorite":
            record["favorite_count"] += 1
        elif event_type == "purchase":
            record["purchase_count"] += 1

    items = []
    for _, record in performance.items():
        recommend_count = max(record["recommend_count"], 1)
        record["click_rate"] = round(record["click_count"] / recommend_count, 2)
        record["purchase_rate"] = round(record["purchase_count"] / recommend_count, 2)
        items.append(record)

    return sorted(items, key=lambda item: (item["recommend_count"], item["click_count"], item["purchase_count"]), reverse=True)[
        :limit
    ]


def summarize_analytics(events: list[dict], feedback_events: list[dict]) -> dict:
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
    average_result_count = round(sum(event.get("result_count", 0) for event in events) / max(len(events), 1), 2)
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
        "top_queries": top_counter_items(query_counter),
        "top_categories": top_counter_items(category_counter),
        "top_products": top_counter_items(product_counter),
        "top_stores": top_counter_items(store_counter),
        "top_feedback_products": top_counter_items(feedback_product_counter),
        "last_event_at": max(last_candidates) if last_candidates else None,
    }


def build_dashboard(events: list[dict], feedback_events: list[dict], limit: int = 5) -> dict:
    summary = summarize_analytics(events, feedback_events)
    return {
        "summary": summary,
        "funnel": {
            "requests": summary["total_requests"],
            "clicks": summary["feedback_counts"]["click"],
            "favorites": summary["feedback_counts"]["favorite"],
            "purchases": summary["feedback_counts"]["purchase"],
        },
        "query_performance": build_query_performance(events, feedback_events, limit=limit),
        "product_performance": build_product_performance(events, feedback_events, limit=limit),
        "recent_searches": events[-limit:][::-1] if limit > 0 else list(reversed(events)),
        "recent_feedback": feedback_events[-limit:][::-1] if limit > 0 else list(reversed(feedback_events)),
    }
