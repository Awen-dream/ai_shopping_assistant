from fastapi import APIRouter

from .routers.analytics import router as analytics_router
from .routers.catalog import router as catalog_router
from .routers.profiles import router as profiles_router
from .routers.search import router as search_router
from .routers.vector_index import router as vector_index_router

router = APIRouter()
router.include_router(search_router, tags=["search"])
router.include_router(profiles_router, tags=["profiles"])
router.include_router(catalog_router, tags=["catalog"])
router.include_router(vector_index_router, tags=["vector-index"])
router.include_router(analytics_router, tags=["analytics"])
