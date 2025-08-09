import logging
from datetime import datetime, timezone
from typing import Any, Optional, Tuple
from asyncpg import Connection

from bot.enums.roles import UserRole, UserRow  # оставил, как есть

logger = logging.getLogger(__name__)


async def add_user(
    conn: Connection,
    *,
    telegram_id: int,
    username: Optional[str] = None,
    language: str = "ru",
    role: str = UserRole.USER.value,
    is_alive: bool = True,
    banned: bool = False,
) -> None:
    await conn.execute(
        """
        INSERT INTO users(telegram_id, username, language, role, is_alive, banned)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (telegram_id) DO NOTHING;
        """,
        telegram_id, username, language, role, is_alive, banned,
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
    logger.info("Row is %s", row)
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
