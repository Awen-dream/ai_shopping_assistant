from functools import lru_cache

from ..multi_agent_coordinator import MultiAgentCoordinator


@lru_cache(maxsize=1)
def get_coordinator():
    return MultiAgentCoordinator()


def reset_runtime_state():
    get_coordinator.cache_clear()
