import logging
from datetime import datetime, timezone
from typing import Any

from bot.enums.roles import UserRole, UserRow
from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

async def add_user(
    conn: AsyncConnection,
    *,
    telegram_id: int,
    username: str | None = None,
    language: str = "ru",
    role: str = UserRole.USER.value,
    is_alive: bool = True,
    banned: bool = False,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO users(telegram_id, username, language, role, is_alive, banned)
                VALUES (
                    %(telegram_id)s,
                    %(username)s,
                    %(language)s,
                    %(role)s,
                    %(is_alive)s,
                    %(banned)s
                )
                ON CONFLICT (telegram_id) DO NOTHING;
            """,
            params={
                "telegram_id": telegram_id,
                "username": username,
                "language": language,
                "role": role,
                "is_alive": is_alive,
                "banned": banned,
            },
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
    conn: AsyncConnection,
    *,
    telegram_id: int,
) -> tuple[Any, ...] | None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
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
                WHERE telegram_id = %s;
            """,
            params=(telegram_id,),
        )
        row = await cursor.fetchone()
    logger.info("Row is %s", row)
    if row is None:
        return None
    return UserRow(*row)

async def change_user_alive_status(
    conn: AsyncConnection,
    *,
    is_alive: bool,
    telegram_id: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET is_alive = %s
                WHERE telegram_id = %s;
            """,
            params=(is_alive, telegram_id)
        )
    logger.info("Updated `is_alive` status to `%s` for user with telegram_id %d", is_alive, telegram_id)

async def change_user_banned_status_by_id(
    conn: AsyncConnection,
    *,
    banned: bool,
    user_id: int  # это внутренний `id` в таблице users.id
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET banned = %s
                WHERE id = %s;
            """, 
            params=(banned, user_id)
        )
    logger.info("Updated `banned` status to `%s` for user with id %d", banned, user_id)


async def change_user_banned_status_by_username(
    conn: AsyncConnection,
    *,
    banned: bool,
    username: str,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET banned = %s
                WHERE username = %s;
            """, 
            params=(banned, username)
        )
    logger.info("Updated `banned` status to `%s` for username %s", banned, username)


async def get_user_alive_status(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> bool | None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                SELECT is_alive FROM users WHERE telegram_id = %s;
            """,
            params=(user_id,),
        )
        row = await cursor.fetchone()
    if row:
        logger.info("The user with id `%s` has the is_alive status %s", user_id, row[0])
    else:
        logger.warning("No user with id `%s` found in the database", user_id)
    return row[0] if row else None


async def get_user_banned_status_by_id(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> bool | None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                SELECT banned FROM users WHERE telegram_id = %s;
            """,
            params=(user_id,),
        )
        row = await cursor.fetchone()
    if row:
        logger.info("The user with id `%s` has the banned status %s", user_id, row[0])
    else:
        logger.warning("No user with id `%s` found in the database", user_id)
    return row[0] if row else None


async def get_user_banned_status_by_username(
    conn: AsyncConnection,
    *,
    username: str,
) -> bool | None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                SELECT banned FROM users WHERE username = %s;
            """,
            params=(username,),
        )
        row = await cursor.fetchone()
    if row:
        logger.info("The user with username `%s` has the banned status %s", username, row[0])
    else:
        logger.warning("No user with username `%s` found in the database", username)
    return row[0] if row else None


async def get_user_role(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> Any | None:  # замените Any на ваш тип UserRole, если необходимо
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                SELECT role FROM users WHERE telegram_id = %s;
            """,
            params=(user_id,),
        )
        row = await cursor.fetchone()
    if row:
        logger.info("The user with id `%s` has the role %s", user_id, row[0])
        # Если у вас есть Enum UserRole, используйте:
        return UserRole(row[0])
    else:
        logger.warning("No user with id `%s` found in the database", user_id)
    return None
