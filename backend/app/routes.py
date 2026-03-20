from fastapi import APIRouter, Query, UploadFile, File
from .multi_agent_coordinator import MultiAgentCoordinator
import shutil, os

router = APIRouter()
coordinator = MultiAgentCoordinator()

@router.get("/multi-agent-task")
def query_products(q: str):
    return coordinator.handle_query(query=q)

@router.post("/multi-agent-task/image")
def query_by_image(file: UploadFile = File(...)):
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    results = coordinator.handle_query(image_path=temp_path)
    os.remove(temp_path)
    return results