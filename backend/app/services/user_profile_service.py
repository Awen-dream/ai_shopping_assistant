import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from app.services.product_service import get_user_profiles_db_path, get_user_profiles_path


class SqliteUserProfileRepository:
    """SQLite-backed repository for persisted user profiles."""

    def __init__(self, db_path: Path | None = None, seed_path: Path | None = None):
        self.db_path = db_path or get_user_profiles_db_path()
        self.seed_path = seed_path or get_user_profiles_path()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection):
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                updated_at TEXT
            )
            """
        )
        connection.commit()

    def _seed_from_json_if_needed(self, connection: sqlite3.Connection):
        row = connection.execute("SELECT COUNT(1) AS count FROM user_profiles").fetchone()
        if row and row["count"] > 0:
            return

        if not self.seed_path.exists():
            return

        with self.seed_path.open("r", encoding="utf-8") as f:
            profiles = json.load(f) or {}

        for user_id, profile in profiles.items():
            connection.execute(
                """
                INSERT OR REPLACE INTO user_profiles (user_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    json.dumps(profile, ensure_ascii=False),
                    profile.get("updated_at"),
                ),
            )
        connection.commit()

    def list_profiles(self) -> dict:
        with self._get_connection() as connection:
            self._ensure_schema(connection)
            self._seed_from_json_if_needed(connection)
            rows = connection.execute("SELECT user_id, profile_json FROM user_profiles").fetchall()

        profiles = {}
        for row in rows:
            try:
                profiles[row["user_id"]] = json.loads(row["profile_json"])
            except json.JSONDecodeError:
                continue
        return profiles

    def get_profile(self, user_id: str) -> dict | None:
        with self._get_connection() as connection:
            self._ensure_schema(connection)
            self._seed_from_json_if_needed(connection)
            row = connection.execute(
                "SELECT profile_json FROM user_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        if not row:
            return None

        try:
            return json.loads(row["profile_json"])
        except json.JSONDecodeError:
            return None

    def upsert_profile(self, user_id: str, profile: dict):
        with self._get_connection() as connection:
            self._ensure_schema(connection)
            connection.execute(
                """
                INSERT OR REPLACE INTO user_profiles (user_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    json.dumps(profile, ensure_ascii=False),
                    profile.get("updated_at"),
                ),
            )
            connection.commit()

    def replace_profiles(self, profiles: dict):
        with self._get_connection() as connection:
            self._ensure_schema(connection)
            connection.execute("DELETE FROM user_profiles")
            for user_id, profile in profiles.items():
                connection.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles (user_id, profile_json, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        user_id,
                        json.dumps(profile, ensure_ascii=False),
                        profile.get("updated_at"),
                    ),
                )
            connection.commit()


@lru_cache(maxsize=1)
def get_user_profile_repository() -> SqliteUserProfileRepository:
    return SqliteUserProfileRepository()


def read_profiles() -> dict:
    return get_user_profile_repository().list_profiles()


def write_profiles(profiles: dict):
    get_user_profile_repository().replace_profiles(profiles)


@lru_cache(maxsize=1)
def list_user_profiles():
    return read_profiles()


def refresh_user_profiles_cache():
    list_user_profiles.cache_clear()
    get_user_profile_repository.cache_clear()


def get_user_profile(user_id: str) -> dict | None:
    from app.domains.profiles.service import get_user_profile as domain_get_user_profile

    return domain_get_user_profile(user_id)


def upsert_user_profile(user_id: str, payload: dict) -> dict:
    from app.domains.profiles.service import upsert_user_profile as domain_upsert_user_profile

    return domain_upsert_user_profile(user_id, payload)


def merge_profiles(base_profile: dict | None, query_profile: dict | None) -> dict:
    from app.domains.profiles.model import merge_profiles as domain_merge_profiles

    return domain_merge_profiles(base_profile, query_profile)
