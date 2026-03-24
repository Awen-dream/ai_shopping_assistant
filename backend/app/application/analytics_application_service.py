from fastapi import HTTPException

from ..domains.analytics import (
    build_feedback_event,
    get_analytics_dashboard,
    get_analytics_summary,
    list_feedback_events,
    list_recommendation_events,
    log_feedback_event,
)


SUPPORTED_FEEDBACK_EVENTS = {"click", "favorite", "purchase"}


class AnalyticsApplicationService:
    def get_summary(self):
        return {"summary": get_analytics_summary()}

    def get_dashboard(self, limit: int = 5):
        return {"dashboard": get_analytics_dashboard(limit=limit)}

    def list_events(self, limit: int = 10):
        return {"events": list_recommendation_events(limit=limit)}

    def list_feedback(self, limit: int = 10):
        return {"events": list_feedback_events(limit=limit)}

    def create_feedback(self, payload: dict):
        event_type = payload["event_type"]
        if event_type not in SUPPORTED_FEEDBACK_EVENTS:
            raise HTTPException(status_code=400, detail="Unsupported feedback event type.")

        event = build_feedback_event(
            event_type=event_type,
            product_id=payload["product_id"],
            product_name=payload.get("product_name", ""),
            query=payload.get("query", ""),
            user_id=payload.get("user_id"),
        )
        log_feedback_event(event)
        return {"event": event, "summary": get_analytics_summary()}
