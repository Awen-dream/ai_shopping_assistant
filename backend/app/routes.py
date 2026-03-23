import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from .multi_agent_coordinator import MultiAgentCoordinator
from .services.analytics_service import (
    build_feedback_event,
    build_recommendation_event,
    get_analytics_summary,
    list_feedback_events,
    list_recommendation_events,
    log_feedback_event,
    log_recommendation_event,
)
from .services.product_service import create_product, delete_product, list_products, upsert_product
from .services.user_profile_service import get_user_profile, upsert_user_profile
from .services.vector_store_service import rebuild_vector_store, sync_vector_store_after_product_change

router = APIRouter()


@lru_cache(maxsize=1)
def get_coordinator():
    return MultiAgentCoordinator()


class UserProfilePayload(BaseModel):
    preferred_brand: list[str] | None = None
    budget_range: list[int] | None = None
    interests: list[str] | None = None
    category: str | None = None
    preferred_categories: list[str] | None = None
    price_sensitivity: str | None = None
    city: str | None = None


class WarehousePayload(BaseModel):
    name: str
    stock: int


class ProductPayload(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    brand: str | None = None
    price: float | None = None
    rating: float | None = None
    tags: list[str] | None = None
    monthly_sales: int | None = None
    promotion_tag: str | None = None
    inventory_total: int | None = None
    warehouses: list[WarehousePayload] | None = None


class FeedbackPayload(BaseModel):
    event_type: str
    product_id: int
    product_name: str | None = None
    query: str | None = None
    user_id: str | None = None


@router.get("/multi-agent-task")
def query_products(q: str = Query(..., min_length=1), user_id: str | None = Query(default=None)):
    results = get_coordinator().handle_query(query=q, user_id=user_id)
    log_recommendation_event(
        build_recommendation_event(
            results,
            query=q,
            user_id=user_id,
            image_search=False,
            vector_status=get_coordinator().get_vector_status(),
        )
    )
    return {"results": results}


@router.post("/multi-agent-task/image")
def query_by_image(file: UploadFile = File(...), user_id: str | None = Form(default=None)):
    suffix = Path(file.filename or "").suffix
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        results = get_coordinator().handle_query(image_path=temp_path, user_id=user_id)
        log_recommendation_event(
            build_recommendation_event(
                results,
                query="",
                user_id=user_id,
                image_search=True,
                vector_status=get_coordinator().get_vector_status(),
            )
        )
        return {"results": results}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/user-profiles/{user_id}")
def read_user_profile(user_id: str):
    return {"profile": get_user_profile(user_id)}


@router.put("/user-profiles/{user_id}")
def save_user_profile(user_id: str, payload: UserProfilePayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    profile = upsert_user_profile(user_id, payload_dict)
    return {"profile": profile}


@router.get("/products")
def read_products():
    return {"products": list_products()}


@router.post("/products")
def create_catalog_product(payload: ProductPayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    product = create_product(payload_dict)
    sync_status = sync_vector_store_after_product_change(list_products())
    get_coordinator.cache_clear()
    return {"product": product, "vector_status": sync_status}


@router.put("/products/{product_id}")
def save_catalog_product(product_id: int, payload: ProductPayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    product = upsert_product(product_id, payload_dict)
    sync_status = sync_vector_store_after_product_change(list_products())
    get_coordinator.cache_clear()
    return {"product": product, "vector_status": sync_status}


@router.delete("/products/{product_id}")
def remove_catalog_product(product_id: int):
    deleted = delete_product(product_id)
    sync_status = sync_vector_store_after_product_change(list_products())
    get_coordinator.cache_clear()
    return {"product": deleted, "vector_status": sync_status}


@router.get("/vector-index/status")
def read_vector_index_status():
    return {"status": get_coordinator().get_vector_status()}


@router.post("/vector-index/rebuild")
def rebuild_vector_index(persist: bool = Query(default=True)):
    status = rebuild_vector_store(list_products(), persist=persist)
    get_coordinator.cache_clear()
    refreshed_status = get_coordinator().get_vector_status()
    return {"status": status, "active_status": refreshed_status}


@router.get("/analytics/summary")
def read_analytics_summary():
    return {"summary": get_analytics_summary()}


@router.get("/analytics/events")
def read_analytics_events(limit: int = Query(default=10, ge=1, le=100)):
    return {"events": list_recommendation_events(limit=limit)}


@router.get("/analytics/feedback")
def read_feedback_events(limit: int = Query(default=10, ge=1, le=100)):
    return {"events": list_feedback_events(limit=limit)}


@router.post("/analytics/feedback")
def create_feedback_event(payload: FeedbackPayload):
    if payload.event_type not in {"click", "favorite", "purchase"}:
        raise HTTPException(status_code=400, detail="Unsupported feedback event type.")

    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    event = build_feedback_event(
        event_type=payload_dict["event_type"],
        product_id=payload_dict["product_id"],
        product_name=payload_dict.get("product_name", ""),
        query=payload_dict.get("query", ""),
        user_id=payload_dict.get("user_id"),
    )
    log_feedback_event(event)
    return {"event": event, "summary": get_analytics_summary()}
