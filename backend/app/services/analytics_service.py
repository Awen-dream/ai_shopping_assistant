import json
from pathlib import Path

from app.services.product_service import DATA_DIR


ANALYTICS_EVENTS_PATH = DATA_DIR / "recommendation_events.jsonl"
ANALYTICS_FEEDBACK_PATH = DATA_DIR / "recommendation_feedback.jsonl"


def get_analytics_events_path() -> Path:
    return ANALYTICS_EVENTS_PATH


def get_analytics_feedback_path() -> Path:
    return ANALYTICS_FEEDBACK_PATH


def append_recommendation_event(event: dict):
    path = get_analytics_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def append_feedback_event(event: dict):
    path = get_analytics_feedback_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def list_recommendation_events(limit: int = 20) -> list[dict]:
    path = get_analytics_events_path()
    if not path.exists():
        return []

    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if limit <= 0:
        return events
    return events[-limit:][::-1]


def list_feedback_events(limit: int = 20) -> list[dict]:
    path = get_analytics_feedback_path()
    if not path.exists():
        return []

    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if limit <= 0:
        return events
    return events[-limit:][::-1]

def get_analytics_summary() -> dict:
    from app.domains.analytics.service import get_analytics_summary as domain_get_analytics_summary

    return domain_get_analytics_summary()


def get_analytics_dashboard(limit: int = 5) -> dict:
    from app.domains.analytics.service import get_analytics_dashboard as domain_get_analytics_dashboard

    return domain_get_analytics_dashboard(limit=limit)


def build_recommendation_event(*args, **kwargs):
    from app.domains.analytics.model import build_recommendation_event as domain_build_recommendation_event

    return domain_build_recommendation_event(*args, **kwargs)


def build_feedback_event(*args, **kwargs):
    from app.domains.analytics.model import build_feedback_event as domain_build_feedback_event

    return domain_build_feedback_event(*args, **kwargs)


def log_recommendation_event(event: dict):
    from app.domains.analytics.service import log_recommendation_event as domain_log_recommendation_event

    return domain_log_recommendation_event(event)


def log_feedback_event(event: dict):
    from app.domains.analytics.service import log_feedback_event as domain_log_feedback_event

    return domain_log_feedback_event(event)
