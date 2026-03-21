import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, File, Query, UploadFile

from .multi_agent_coordinator import MultiAgentCoordinator

router = APIRouter()


@lru_cache(maxsize=1)
def get_coordinator():
    return MultiAgentCoordinator()


@router.get("/multi-agent-task")
def query_products(q: str = Query(..., min_length=1)):
    results = get_coordinator().handle_query(query=q)
    return {"results": results}


@router.post("/multi-agent-task/image")
def query_by_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        results = get_coordinator().handle_query(image_path=temp_path)
        return {"results": results}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
