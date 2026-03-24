from .runtime import get_coordinator
from ..domains.analytics import (
    build_recommendation_event,
    log_recommendation_event,
)


class QueryApplicationService:
    """Coordinates recommendation requests and related analytics logging."""

    def handle_text_query(self, query: str, user_id: str | None = None):
        coordinator = get_coordinator()
        results = coordinator.handle_query(query=query, user_id=user_id)
        log_recommendation_event(
            build_recommendation_event(
                results,
                query=query,
                user_id=user_id,
                image_search=False,
                vector_status=coordinator.get_vector_status(),
            )
        )
        return results

    def handle_image_query(self, image_path: str, user_id: str | None = None):
        coordinator = get_coordinator()
        results = coordinator.handle_query(image_path=image_path, user_id=user_id)
        log_recommendation_event(
            build_recommendation_event(
                results,
                query="",
                user_id=user_id,
                image_search=True,
                vector_status=coordinator.get_vector_status(),
            )
        )
        return results

    def get_vector_status(self):
        return get_coordinator().get_vector_status()
