import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def isolate_repo_data():
    from app import routes
    from app.services.analytics_service import get_analytics_events_path, get_analytics_feedback_path
    from app.services.product_service import (
        get_product_index_path,
        get_products_path,
        get_recommendation_eval_cases_path,
        get_user_profiles_db_path,
        get_user_profiles_path,
        refresh_products_cache,
    )
    from app.services.user_profile_service import refresh_user_profiles_cache
    from app.services.vector_store_service import (
        get_product_index_metadata_path,
        set_runtime_vector_store_override,
    )

    tracked_paths = [
        get_products_path(),
        get_recommendation_eval_cases_path(),
        get_user_profiles_path(),
        get_user_profiles_db_path(),
        get_product_index_path(),
        get_product_index_metadata_path(),
        get_analytics_events_path(),
        get_analytics_feedback_path(),
    ]
    analytics_paths = {
        get_analytics_events_path(),
        get_analytics_feedback_path(),
    }
    snapshots = {}
    for path in tracked_paths:
        snapshots[path] = path.read_bytes() if path.exists() else None
        if path in analytics_paths and path.exists():
            path.unlink()

    try:
        yield
    finally:
        for path, content in snapshots.items():
            if content is None:
                if path.exists():
                    path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

        refresh_products_cache()
        refresh_user_profiles_cache()
        set_runtime_vector_store_override(None)
        routes.get_coordinator.cache_clear()
