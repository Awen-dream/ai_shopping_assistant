from fastapi import APIRouter

from ..dependencies import get_profile_application_service
from ..schemas import UserProfilePayload

router = APIRouter()


@router.get("/user-profiles/{user_id}")
def read_user_profile(user_id: str):
    return get_profile_application_service().get_profile(user_id)


@router.put("/user-profiles/{user_id}")
def save_user_profile(user_id: str, payload: UserProfilePayload):
    payload_dict = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    return get_profile_application_service().save_profile(user_id, payload_dict)
