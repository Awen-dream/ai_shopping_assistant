from fastapi import APIRouter, Query

from ..dependencies import get_analytics_application_service, get_evaluation_application_service
from ..schemas import FeedbackPayload

router = APIRouter()


@router.get("/analytics/summary")
def read_analytics_summary():
    return get_analytics_application_service().get_summary()


@router.get("/analytics/dashboard")
def read_analytics_dashboard(limit: int = Query(default=5, ge=1, le=20)):
    return get_analytics_application_service().get_dashboard(limit=limit)


@router.get("/analytics/events")
def read_analytics_events(limit: int = Query(default=10, ge=1, le=100)):
    return get_analytics_application_service().list_events(limit=limit)


@router.get("/analytics/feedback")
def read_feedback_events(limit: int = Query(default=10, ge=1, le=100)):
    return get_analytics_application_service().list_feedback(limit=limit)


@router.post("/analytics/feedback")
def create_feedback_event(payload: FeedbackPayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    return get_analytics_application_service().create_feedback(payload_dict)


@router.get("/analytics/evaluation")
def read_recommendation_evaluation():
    return {"evaluation": get_evaluation_application_service().run_recommendation_evaluation()}
