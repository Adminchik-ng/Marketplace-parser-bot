import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from asyncpg import Connection

from enums.roles import UserRole, UserRow

logger = logging.getLogger(__name__)


async def add_user(
    conn: Connection,
    *,
    telegram_id: int,
    chat_id: int = None,
    username: Optional[str] = None,
    language: str = "ru",
    role: str = UserRole.USER.value,
    is_alive: bool = True,
    banned: bool = False,
) -> None:
    await conn.execute(
        """
        INSERT INTO users(telegram_id, chat_id, username, language, role, is_alive, banned)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (telegram_id) DO NOTHING;
        """,
        telegram_id, chat_id, username, language, role, is_alive, banned,
    )
    logger.info(
        "User added. Table=`users`, telegram_id=%d, created_at='%s', "
        "language='%s', role=%s, is_alive=%s, banned=%s",
        telegram_id,
        datetime.now(timezone.utc),
        language,
        role,
        is_alive,
        banned,
    )


async def get_user(
    conn: Connection,
    *,
    telegram_id: int,
) -> Optional[UserRow]:
    row = await conn.fetchrow(
        """
        SELECT 
            id,
            telegram_id,
            chat_id,
            username,
            language,
            role,
            is_alive,
            banned,
            created_at,
            updated_at
        FROM users 
        WHERE telegram_id = $1;
        """,
        telegram_id,
    )
    logger.info("Finded user with telegram_id %d", telegram_id)
    if row is None:
        return None
    return UserRow(*row)


async def change_user_alive_status(
    conn: Connection,
    *,
    is_alive: bool,
    telegram_id: int,
) -> None:
    await conn.execute(
        """
        UPDATE users
        SET is_alive = $1
        WHERE telegram_id = $2;
        """,
        is_alive, telegram_id,
    )
    logger.info(
        "Updated `is_alive` status to `%s` for user with telegram_id %d",
        is_alive,
        telegram_id,
    )


async def change_user_banned_status_by_id(
    conn: Connection,
    *,
    banned: bool,
    user_id: int,  # внутренний id users.id
) -> None:
    await conn.execute(
        """
        UPDATE users
        SET banned = $1
        WHERE id = $2;
        """, 
        banned, user_id,
    )
    logger.info("Updated `banned` status to `%s` for user with id %d", banned, user_id)


async def change_user_banned_status_by_username(
    conn: Connection,
    *,
    banned: bool,
    username: str,
) -> None:
    await conn.execute(
        """
        UPDATE users
        SET banned = $1
        WHERE username = $2;
        """, 
        banned, username,
    )
    logger.info("Updated `banned` status to `%s` for username %s", banned, username)


async def get_user_alive_status(
    conn: Connection,
    *,
    user_id: int,
) -> Optional[bool]:
    row = await conn.fetchrow(
        """
        SELECT is_alive FROM users WHERE telegram_id = $1;
        """,
        user_id,
    )
    if row:
        logger.info("The user with id `%s` has the is_alive status %s", user_id, row["is_alive"])
        return row["is_alive"]
    else:
        logger.warning("No user with id `%s` found in the database", user_id)
        return None


async def get_user_banned_status_by_id(
    conn: Connection,
    *,
    user_id: int,
) -> Optional[bool]:
    row = await conn.fetchrow(
        """
        SELECT banned FROM users WHERE telegram_id = $1;
        """,
        user_id,
    )
    if row:
        logger.info("The user with id `%s` has the banned status %s", user_id, row["banned"])
        return row["banned"]
    else:
        logger.warning("No user with id `%s` found in the database", user_id)
        return None


async def get_user_banned_status_by_username(
    conn: Connection,
    *,
    username: str,
) -> Optional[bool]:
    row = await conn.fetchrow(
        """
        SELECT banned FROM users WHERE username = $1;
        """,
        username,
    )
    if row:
        logger.info("The user with username `%s` has the banned status %s", username, row["banned"])
        return row["banned"]
    else:
        logger.warning("No user with username `%s` found in the database", username)
        return None


async def get_user_role(
    conn: Connection,
    *,
    user_id: int,
) -> Optional[UserRole]:
    row = await conn.fetchrow(
        """
        SELECT role FROM users WHERE telegram_id = $1;
        """,
        user_id,
    )
    if row:
        logger.info("The user with id `%s` has the role %s", user_id, row["role"])
        return UserRole(row["role"])
    else:
        logger.warning("No user with id `%s` found in the database", user_id)
        return None

async def get_user_chat_id(
    conn: Connection,
    *,
    user_id: int,
) -> Optional[str]:
    row = await conn.fetchrow(
        """
        SELECT chat_id FROM users WHERE telegram_id = $1;
        """,
        user_id,
    )
    if row:
        logger.info("The user with id `%s` has the chat_id=%s", user_id, row["chat_id"])
        return row["chat_id"]
    else:
        logger.warning("No chat_id for user with id `%s` found in the database", user_id)
        return None
    
# Общее количество зарегистрированных пользователей
async def get_total_users(conn: Connection) -> Optional[int]:
    row = await conn.fetchrow("SELECT COUNT(*) AS total FROM users;")
    logger.info("Total users count retrieved")
    if row:
        return row["total"]
    return None

# Распределение пользователей по ролям и статусу banned
async def get_users_role_distribution(conn: Connection) -> Optional[List[Tuple[str, bool, int]]]:
    rows = await conn.fetch(
        """
        SELECT role, banned, COUNT(*) AS count
        FROM users
        GROUP BY role, banned;
        """
    )
    logger.info("Users role distribution retrieved")
    if rows:
        return [(row["role"], row["banned"], row["count"]) for row in rows]
    return None

# Процент новых пользователей за последние 7 дней
async def get_percent_new_users_week(conn: Connection) -> Optional[float]:
    row = await conn.fetchrow(
        """
        SELECT 
            (COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days')) * 100.0 / COUNT(*) AS percent_new
        FROM users;
        """
    )
    logger.info("Percent of new users this week retrieved")
    if row:
        return row["percent_new"]
    return None