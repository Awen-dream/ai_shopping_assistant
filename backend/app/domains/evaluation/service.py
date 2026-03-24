import json

from ...services.product_service import get_recommendation_eval_cases_path


def load_evaluation_cases() -> list[dict]:
    path = get_recommendation_eval_cases_path()
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return json.load(f) or []
