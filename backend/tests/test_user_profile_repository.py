from app.services.product_service import get_user_profiles_db_path
from app.services.user_profile_service import get_user_profile_repository, refresh_user_profiles_cache


def test_profile_repository_seeds_sqlite_from_json():
    refresh_user_profiles_cache()
    repository = get_user_profile_repository()

    profile = repository.get_profile("demo_student")

    assert profile is not None
    assert profile["city"] == "Hangzhou"
    assert get_user_profiles_db_path().exists()


def test_profile_repository_upsert_persists_single_profile():
    refresh_user_profiles_cache()
    repository = get_user_profile_repository()

    repository.upsert_profile(
        "repo_user",
        {
            "user_id": "repo_user",
            "preferred_brand": ["Apple"],
            "favorite_brands": ["Apple"],
            "budget_range": [1000, 8000],
            "interests": ["轻便"],
            "preferred_categories": ["耳机"],
            "recent_categories": ["耳机"],
            "recent_clicked_product_ids": [2, 9],
            "price_sensitivity": "medium",
            "price_band_preference": "mid",
            "city": "Suzhou",
            "updated_at": "2026-03-24T00:00:00+08:00",
        },
    )
    refresh_user_profiles_cache()

    saved = repository.get_profile("repo_user")

    assert saved is not None
    assert saved["preferred_brand"] == ["Apple"]
    assert saved["recent_clicked_product_ids"] == [2, 9]
    assert saved["price_band_preference"] == "mid"
    assert saved["city"] == "Suzhou"
