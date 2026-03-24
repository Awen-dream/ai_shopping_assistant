from .runtime import get_coordinator, reset_runtime_state
from ..domains.catalog import list_products
from ..domains.vector_index import rebuild_vector_store


class VectorApplicationService:
    def get_status(self):
        return {"status": get_coordinator().get_vector_status()}

    def rebuild(self, persist: bool = True):
        status = rebuild_vector_store(list_products(), persist=persist)
        reset_runtime_state()
        refreshed_status = get_coordinator().get_vector_status()
        return {"status": status, "active_status": refreshed_status}
