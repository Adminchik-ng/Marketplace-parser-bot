import logging
from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

async def add_product(
    conn: AsyncConnection,
    *,
    user_id: int,
    marketplace: str,
    product_url: str,
    target_price: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO products (user_id, marketplace, product_url, target_price)
            VALUES (%s, %s, %s, %s);
            """,
            (user_id, marketplace, product_url, target_price),
        )
    logger.info(
        "Product added: user_id=%d, marketplace=%s, url=%s, target_price=%d",
        user_id, marketplace, product_url, target_price
    )
    
async def get_user_active_products(
    conn: AsyncConnection,
    *,
    user_id: int,
) -> list[tuple[int, str | None, str]]:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            SELECT product_id, product_name, product_url, target_price
            FROM products
            WHERE user_id = %s AND is_active = TRUE;
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_product_by_id_and_user(
    conn: AsyncConnection,
    *,
    product_id: int,
    user_id: int,
) -> tuple[str | None, str] | None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            SELECT product_name, product_url
            FROM products
            WHERE product_id = %s AND user_id = %s AND is_active = TRUE;
            """,
            (product_id, user_id),
        )
        return await cursor.fetchone()


async def delete_product_by_id(
    conn: AsyncConnection,
    *,
    product_id: int,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM products WHERE product_id = %s;",
            (product_id,),
        )
    logger.info("Product deleted product_id=%d", product_id)

async def get_user_active_products_with_prices(
    conn: AsyncConnection,
    *,
    user_id: int
) -> list[tuple[int, str | None, str, int, int, int, str]]:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            SELECT product_id, product_name, product_url, target_price, current_price, min_price, marketplace
            FROM products
            WHERE user_id = %s AND is_active = TRUE;
            """,
            (user_id,),
        )
        return await cursor.fetchall()
