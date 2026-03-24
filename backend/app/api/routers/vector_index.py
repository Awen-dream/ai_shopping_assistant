from fastapi import APIRouter, Query

from ..dependencies import get_vector_application_service

router = APIRouter()


@router.get("/vector-index/status")
def read_vector_index_status():
    return get_vector_application_service().get_status()


@router.post("/vector-index/rebuild")
def rebuild_vector_index(persist: bool = Query(default=True)):
    return get_vector_application_service().rebuild(persist=persist)
