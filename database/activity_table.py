import logging
from datetime import datetime, timezone
from typing import Any

from bot.enums.roles import UserRole, UserRow
from psycopg import AsyncConnection

logger = logging.getLogger(__name__)


async def add_user_activity(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> None:
    async with conn.cursor() as cursor:
        # Проверяем, есть ли запись за сегодня
        await cursor.execute(
            query="""
                SELECT id FROM activity WHERE user_id = %s AND activity_date = CURRENT_DATE;
            """,
            params=(user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            # Нет записи — вставляем новую со actions = 1
            await cursor.execute(
                query="""
                    INSERT INTO activity (user_id, activity_date, actions)
                    VALUES (%s, CURRENT_DATE, 1);
                """,
                params=(user_id,)
            )
        else:
            # Есть запись — обновляем actions
            await cursor.execute(
                query="""
                    UPDATE activity
                    SET actions = actions + 1
                    WHERE user_id = %s AND activity_date = CURRENT_DATE;
                """,
                params=(user_id,)
            )
    logger.info("User activity updated. user_id=%d", user_id)

async def get_statistics(
    conn: AsyncConnection,
) -> list[Any] | None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                SELECT user_id, SUM(actions) AS total_actions
                FROM activity
                GROUP BY user_id
                ORDER BY total_actions DESC
                LIMIT 5;
            """,
        )
        rows = await cursor.fetchall()
    logger.info("Users activity retrieved from table=`activity`")
    return rows if rows else None