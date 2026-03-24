from ..domains.profiles import get_user_profile, upsert_user_profile


class ProfileApplicationService:
    def get_profile(self, user_id: str):
        return {"profile": get_user_profile(user_id)}

    def save_profile(self, user_id: str, payload: dict):
        profile = upsert_user_profile(user_id, payload)
        return {"profile": profile}
