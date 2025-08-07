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
        await cursor.execute(
            query="""
                INSERT INTO activity (user_id)
                VALUES (%s)
                ON CONFLICT (user_id, activity_date)
                DO UPDATE SET actions = activity.actions + 1;
            """,
            params=(user_id,),
        )
    logger.info("User activity updated. table=`activity`, user_id=%d", user_id)


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