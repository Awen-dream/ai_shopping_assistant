from functools import lru_cache

from ..application.analytics_application_service import AnalyticsApplicationService
from ..application.catalog_application_service import CatalogApplicationService
from ..application.evaluation_application_service import EvaluationApplicationService
from ..application.profile_application_service import ProfileApplicationService
from ..application.query_application_service import QueryApplicationService
from ..application.vector_application_service import VectorApplicationService


@lru_cache(maxsize=1)
def get_query_application_service():
    return QueryApplicationService()


@lru_cache(maxsize=1)
def get_catalog_application_service():
    return CatalogApplicationService()


@lru_cache(maxsize=1)
def get_profile_application_service():
    return ProfileApplicationService()


@lru_cache(maxsize=1)
def get_vector_application_service():
    return VectorApplicationService()


@lru_cache(maxsize=1)
def get_analytics_application_service():
    return AnalyticsApplicationService()


@lru_cache(maxsize=1)
def get_evaluation_application_service():
    return EvaluationApplicationService()
