import logging
from typing import Optional, Tuple
from asyncpg import Connection

logger = logging.getLogger(__name__)


async def get_user_role_and_active_products_count(
    conn: Connection,
    *,
    user_id: int,
) -> Optional[Tuple[str, int]]:
    try:
        row = await conn.fetchrow(
            """
            SELECT
                u.role,
                COUNT(p.product_id) AS products_count
            FROM
                users u
            LEFT JOIN
                products p ON u.telegram_id = p.user_id AND p.is_active = TRUE
            WHERE
                u.telegram_id = $1
            GROUP BY
                u.role;
            """,
            user_id,
        )
        if row:
            logger.info(f"User {user_id} role: {row['role']}, active products count: {row['products_count']}")
            return row["role"], row["products_count"]
        else:
            logger.warning(f"User {user_id} not found in DB")
            return None
    except Exception as e:
        logger.error(f"Error fetching user role and active products count for user {user_id}: {e}", exc_info=True)
        return None