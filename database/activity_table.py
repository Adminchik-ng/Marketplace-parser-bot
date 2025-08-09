import logging
from typing import Any, Optional, List, Tuple
from asyncpg import Connection

logger = logging.getLogger(__name__)


async def add_user_activity(
    conn: Connection,
    *,
    user_id: int,
) -> None:
    # Проверяем, есть ли запись за сегодня
    row = await conn.fetchrow(
        """
        SELECT id FROM activity WHERE user_id = $1 AND activity_date = CURRENT_DATE;
        """,
        user_id,
    )
    if row is None:
        # Нет записи — вставляем новую со actions = 1
        await conn.execute(
            """
            INSERT INTO activity (user_id, activity_date, actions)
            VALUES ($1, CURRENT_DATE, 1);
            """,
            user_id,
        )
    else:
        # Есть запись — обновляем actions
        await conn.execute(
            """
            UPDATE activity
            SET actions = actions + 1
            WHERE user_id = $1 AND activity_date = CURRENT_DATE;
            """,
            user_id,
        )
    logger.info("User activity updated. user_id=%d", user_id)


async def get_statistics(
    conn: Connection,
) -> Optional[List[Tuple[int, int]]]:
    rows = await conn.fetch(
        """
        SELECT user_id, SUM(actions) AS total_actions
        FROM activity
        GROUP BY user_id
        ORDER BY total_actions DESC
        LIMIT 5;
        """
    )
    logger.info("Users activity retrieved from table=`activity`")
    if rows:
        # Преобразуем в список кортежей (user_id, total_actions)
        return [(row["user_id"], row["total_actions"]) for row in rows]
    return None
