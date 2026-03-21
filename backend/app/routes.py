import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, File, Form, Query, UploadFile
from pydantic import BaseModel

from .multi_agent_coordinator import MultiAgentCoordinator
from .services.product_service import list_products
from .services.user_profile_service import get_user_profile, upsert_user_profile
from .services.vector_store_service import rebuild_vector_store

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


@router.get("/multi-agent-task")
def query_products(q: str = Query(..., min_length=1), user_id: str | None = Query(default=None)):
    results = get_coordinator().handle_query(query=q, user_id=user_id)
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


@router.get("/vector-index/status")
def read_vector_index_status():
    return {"status": get_coordinator().get_vector_status()}


@router.post("/vector-index/rebuild")
def rebuild_vector_index(persist: bool = Query(default=True)):
    status = rebuild_vector_store(list_products(), persist=persist)
    get_coordinator.cache_clear()
    refreshed_status = get_coordinator().get_vector_status()
    return {"status": status, "active_status": refreshed_status}
