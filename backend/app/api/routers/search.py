import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Query, UploadFile

from ..dependencies import get_query_application_service

router = APIRouter()


@router.get("/multi-agent-task")
def query_products(q: str = Query(..., min_length=1), user_id: str | None = Query(default=None)):
    return {"results": get_query_application_service().handle_text_query(q, user_id=user_id)}


@router.post("/multi-agent-task/image")
def query_by_image(file: UploadFile = File(...), user_id: str | None = Form(default=None)):
    suffix = Path(file.filename or "").suffix
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        results = get_query_application_service().handle_image_query(temp_path, user_id=user_id)
        return {"results": results}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
