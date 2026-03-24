from fastapi import APIRouter

from ..dependencies import get_catalog_application_service
from ..schemas import ProductPayload

router = APIRouter()


@router.get("/products")
def read_products():
    return {"products": get_catalog_application_service().list_products()}


@router.post("/products")
def create_catalog_product(payload: ProductPayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    return get_catalog_application_service().create_product(payload_dict)


@router.put("/products/{product_id}")
def save_catalog_product(product_id: int, payload: ProductPayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    return get_catalog_application_service().update_product(product_id, payload_dict)


@router.delete("/products/{product_id}")
def remove_catalog_product(product_id: int):
    return get_catalog_application_service().delete_product(product_id)
