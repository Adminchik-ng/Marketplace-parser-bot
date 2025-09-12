from asyncpg import Connection
from typing import Optional
from enums.roles import UserRow
from datetime import datetime


async def get_user_test(
    conn: Connection,
    telegram_id: int,
) -> Optional[dict]:
    query = """
        SELECT id, telegram_id, chat_id, username, language, role, is_alive, banned, created_at, updated_at
        FROM users
        WHERE telegram_id = $1;
    """
    row = await conn.fetchrow(query, telegram_id)
    if row:
        return UserRow(*row)
    return None


async def add_user_test(
    conn: Connection,
    *,
    telegram_id: int,
    chat_id: int = None,
    username: Optional[str] = None,
    language: str = "ru",
    role: str,
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
   
    
async def add_user_test_default_test(conn: Connection, telegram_id: int = 1) -> None:
    await conn.execute(
        """
        INSERT INTO users(telegram_id, chat_id, username, language, role, is_alive, banned)
        VALUES ($1, 123, 'default_username', 'ru', 'user', TRUE, FALSE)
        ON CONFLICT (telegram_id) DO NOTHING;
        """,
        telegram_id,
    )


async def add_product_test(
    conn: Connection,
    *,
    user_id: int,
    product_name: str,
    product_url: str,
    target_price: int,
    is_active: bool = True,
    last_error: Optional[str] = None,
    marketplace: str,
) -> None:
    await conn.execute(
        """
        INSERT INTO products (user_id, product_name, product_url, target_price, marketplace, is_active, last_error)
        VALUES ($1, $2, $3, $4, $5, $6, $7);
        """,
        user_id, product_name, product_url, target_price, marketplace, is_active, last_error
    )
 
 
async def update_user_created_at_test(conn: Connection, telegram_id: int, created_at: datetime) -> None:

    await conn.execute(
        "UPDATE users SET created_at = $1 WHERE telegram_id = $2",
        created_at, telegram_id
    )


async def get_user_activity_actions_test(conn: Connection, user_id: int) -> int | None:
    row = await conn.fetchrow(
        "SELECT actions FROM activity WHERE user_id = $1 AND activity_date = CURRENT_DATE",
        user_id,
    )
    if row:
        return row["actions"]
    return None


async def insert_activity_test(conn: Connection, user_id: int, actions: int = 1) -> None:
    await conn.execute(
        """
        INSERT INTO activity (user_id, activity_date, actions)
        VALUES ($1, CURRENT_DATE, $2);
        """,
        user_id,
        actions,
    )


async def get_product_by_user_id_test(conn: Connection, user_id: int):
    row = await conn.fetchrow(
        "SELECT user_id, marketplace, product_url, target_price FROM products WHERE user_id = $1",
        user_id,
    )
    return row


async def get_products_count_test(conn: Connection):
    row = await conn.fetchrow(
        "SELECT COUNT(*) as count FROM products",
    )
    return row['count']


async def get_product_active_status_id_test(conn: Connection, user_id: int):
    row = await conn.fetchrow(
        "SELECT is_active FROM products WHERE user_id = $1",
        user_id,
    )
    return row['is_active']


async def get_product_after_parsing_test(conn: Connection, user_id: int):
    row = await conn.fetchrow(
        "SELECT current_price, product_name, min_price, last_error, is_active FROM products WHERE user_id = $1",
        user_id,
    )
    return row


