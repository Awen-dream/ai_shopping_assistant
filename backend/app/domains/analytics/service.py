from ...services.analytics_service import (
    append_feedback_event,
    append_recommendation_event,
    list_feedback_events as list_feedback_events_store,
    list_recommendation_events as list_recommendation_events_store,
)
from .model import (
    build_dashboard,
    build_feedback_event,
    build_recommendation_event,
    summarize_analytics,
)


def log_recommendation_event(event: dict):
    append_recommendation_event(event)


def log_feedback_event(event: dict):
    append_feedback_event(event)


def list_recommendation_events(limit: int = 20) -> list[dict]:
    return list_recommendation_events_store(limit=limit)


def list_feedback_events(limit: int = 20) -> list[dict]:
    return list_feedback_events_store(limit=limit)


def get_analytics_summary() -> dict:
    events = list_recommendation_events_store(limit=0)
    feedback_events = list_feedback_events_store(limit=0)
    return summarize_analytics(events, feedback_events)


def get_analytics_dashboard(limit: int = 5) -> dict:
    events = list_recommendation_events_store(limit=0)
    feedback_events = list_feedback_events_store(limit=0)
    return build_dashboard(events, feedback_events, limit=limit)
