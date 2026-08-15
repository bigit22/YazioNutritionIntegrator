import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from app.config import settings
from app.models import NutritionResult

_pool: asyncpg.Pool | None = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS meal_logs (
    id UUID PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    source_message_id BIGINT,
    meal_type TEXT NOT NULL,
    description TEXT NOT NULL,
    user_text TEXT,
    calories DOUBLE PRECISION NOT NULL,
    protein DOUBLE PRECISION NOT NULL,
    fat DOUBLE PRECISION NOT NULL,
    carbs DOUBLE PRECISION NOT NULL,
    portion_grams DOUBLE PRECISION,
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_raw JSONB NOT NULL,
    yazio_consumed_item_id UUID,
    yazio_synced_at TIMESTAMPTZ,
    yazio_payload JSONB,
    yazio_last_error TEXT,
    consumed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_meal_logs_user_consumed_at
    ON meal_logs (telegram_user_id, consumed_at DESC);
"""


async def init_db() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=5)
    async with _pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool


def _parse_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict | list)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return value


def _row_to_meal(row: asyncpg.Record | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "telegram_user_id": row["telegram_user_id"],
        "meal_type": row["meal_type"],
        "description": row["description"],
        "calories": row["calories"],
        "protein": row["protein"],
        "fat": row["fat"],
        "carbs": row["carbs"],
        "portion_grams": row["portion_grams"],
        "items": _parse_json(row["items"], []),
        "yazio_consumed_item_id": (
            str(row["yazio_consumed_item_id"]) if row["yazio_consumed_item_id"] else None
        ),
        "yazio_synced_at": row["yazio_synced_at"],
        "yazio_last_error": row["yazio_last_error"],
        "consumed_at": row["consumed_at"],
        "deleted_at": row["deleted_at"],
    }


class MealRepository:
    async def create_meal(
        self,
        *,
        telegram_user_id: int,
        chat_id: int,
        source_message_id: int,
        meal_type: str,
        user_text: str | None,
        nutrition: NutritionResult,
        consumed_at: datetime,
    ) -> dict:
        meal_id = uuid4()
        query = """
            INSERT INTO meal_logs (
                id, telegram_user_id, chat_id, source_message_id, meal_type,
                description, user_text, calories, protein, fat, carbs,
                portion_grams, items, ai_raw, consumed_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                    $12, $13::jsonb, $14::jsonb, $15)
            RETURNING *
        """
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                meal_id,
                telegram_user_id,
                chat_id,
                source_message_id,
                meal_type,
                nutrition.description,
                user_text,
                float(nutrition.calories),
                float(nutrition.protein),
                float(nutrition.fat),
                float(nutrition.carbs),
                float(nutrition.portion_grams) if nutrition.portion_grams is not None else None,
                json.dumps(nutrition.items),
                nutrition.model_dump_json(),
                consumed_at,
            )
        return _row_to_meal(row)

    async def get_meal(self, meal_id: str, telegram_user_id: int) -> dict | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM meal_logs WHERE id = $1 AND telegram_user_id = $2 LIMIT 1",
                UUID(meal_id),
                telegram_user_id,
            )
        return _row_to_meal(row)

    async def mark_yazio_synced(self, meal_id: str, remote_id: str, payload: dict) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE meal_logs
                SET yazio_consumed_item_id = $2,
                    yazio_synced_at = $3,
                    yazio_payload = $4::jsonb,
                    yazio_last_error = NULL
                WHERE id = $1
                """,
                UUID(meal_id),
                UUID(remote_id),
                datetime.now(UTC),
                json.dumps(payload),
            )

    async def mark_yazio_error(self, meal_id: str, error_text: str) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE meal_logs SET yazio_last_error = $2 WHERE id = $1",
                UUID(meal_id),
                error_text[:500],
            )

    async def soft_delete_meal(self, meal_id: str) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE meal_logs SET deleted_at = $2 WHERE id = $1",
                UUID(meal_id),
                datetime.now(UTC),
            )

    async def list_day_meals(
        self, telegram_user_id: int, start_dt: datetime, end_dt: datetime
    ) -> list[dict]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM meal_logs
                WHERE telegram_user_id = $1
                  AND deleted_at IS NULL
                  AND consumed_at >= $2
                  AND consumed_at < $3
                ORDER BY consumed_at ASC
                """,
                telegram_user_id,
                start_dt,
                end_dt,
            )
        return [_row_to_meal(r) for r in rows if r is not None]

    async def get_day_totals(
        self, telegram_user_id: int, start_dt: datetime, end_dt: datetime
    ) -> dict:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    COALESCE(SUM(calories), 0) AS calories,
                    COALESCE(SUM(protein), 0) AS protein,
                    COALESCE(SUM(fat), 0) AS fat,
                    COALESCE(SUM(carbs), 0) AS carbs,
                    COUNT(*)::int AS meal_count
                FROM meal_logs
                WHERE telegram_user_id = $1
                  AND deleted_at IS NULL
                  AND consumed_at >= $2
                  AND consumed_at < $3
                """,
                telegram_user_id,
                start_dt,
                end_dt,
            )
        return {
            "calories": float(row["calories"]),
            "protein": float(row["protein"]),
            "fat": float(row["fat"]),
            "carbs": float(row["carbs"]),
            "meal_count": int(row["meal_count"]),
        }
