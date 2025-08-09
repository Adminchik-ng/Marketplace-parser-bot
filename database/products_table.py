import logging
from typing import List, Optional, Tuple
from asyncpg import Connection

logger = logging.getLogger(__name__)


async def add_product(
    conn: Connection,
    *,
    user_id: int,
    marketplace: str,
    product_url: str,
    target_price: int,
) -> None:
    await conn.execute(
        """
        INSERT INTO products (user_id, marketplace, product_url, target_price)
        VALUES ($1, $2, $3, $4);
        """,
        user_id, marketplace, product_url, target_price,
    )
    logger.info(
        "Product added: user_id=%d, marketplace=%s, url=%s, target_price=%d",
        user_id, marketplace, product_url, target_price,
    )


async def get_user_active_products(
    conn: Connection,
    *,
    user_id: int,
) -> List[Tuple[int, Optional[str], str, int]]:
    rows = await conn.fetch(
        """
        SELECT product_id, product_name, product_url, target_price
        FROM products
        WHERE user_id = $1 AND is_active = TRUE;
        """,
        user_id,
    )
    return [
        (r["product_id"], r["product_name"], r["product_url"], r["target_price"]) 
        for r in rows
    ]

async def get_user_inactive_products(
    conn: Connection,
    *,
    user_id: int,
) -> List[Tuple[int, Optional[str], str]]:
    rows = await conn.fetch(
        """
        SELECT product_id, product_name, product_url, target_price
        FROM products
        WHERE user_id = $1 AND is_active = FALSE;
        """,
        user_id,
    )
    return [
        (r["product_id"], r["product_name"], r["product_url"], r["target_price"]) 
        for r in rows
    ]
    
async def get_product_by_id_and_user(
    conn: Connection,
    *,
    product_id: int,
    user_id: int,
) -> Optional[Tuple[Optional[str], str]]:
    row = await conn.fetchrow(
        """
        SELECT product_name, product_url
        FROM products
        WHERE product_id = $1 AND user_id = $2 AND is_active = TRUE;
        """,
        product_id, user_id,
    )
    if row:
        return row["product_name"], row["product_url"]
    return None


async def delete_product_by_id(
    conn: Connection,
    *,
    product_id: int,
) -> None:
    await conn.execute(
        """
        DELETE FROM products WHERE product_id = $1;
        """,
        product_id,
    )
    logger.info("Product deleted product_id=%d", product_id)


async def get_user_active_products_with_prices_and_errors(
    conn: Connection,
    *,
    user_id: int,
) -> List[Tuple[int, Optional[str], str, int, int, int, str, str]]:
    rows = await conn.fetch(
        """
        SELECT product_id, product_name, product_url, target_price, current_price, min_price, marketplace, last_error, last_checked
        FROM products
        WHERE user_id = $1;
        """,
        user_id,
    )
    # Возвращаем список кортежей с нужными полями
    return [
        (
            r["product_id"],
            r["product_name"],
            r["product_url"],
            r["target_price"],
            r["current_price"],
            r["min_price"],
            r["marketplace"],
            r["last_error"],
            r["last_checked"],
        )
        for r in rows
    ]


async def change_product_active_status(
    conn: Connection,
    *,
    is_active: bool,
    product_id: int,
) -> None:
    await conn.execute(
        """
        UPDATE products
        SET is_active = $1
        WHERE product_id = $2;
        """,
        is_active, product_id,
    )
    logger.info("Product alive status changed to `%s` for product_id=%d", is_active, product_id)


async def get_products_items_for_parsing(
    conn: Connection,
) -> List[Tuple[int, str, str, int]]:
    rows = await conn.fetch(
        """
        SELECT product_id, product_url, marketplace, min_price
        FROM products
        WHERE is_active = TRUE;
        """
    )
    return [(r["product_id"], r["product_url"], r["marketplace"], r["min_price"]) for r in rows]


async def change_product_price_and_error(
    conn: Connection,
    *,
    product_id: int,
    current_price: int,
    product_name: Optional[str],
    min_price: int,
    last_error: str,
    is_active: bool,
) -> None:
    await conn.execute(
        """
        UPDATE products
        SET current_price = $1,
            product_name = $2,
            min_price = $3,
            last_checked = now(),
            last_error = $4,
            is_active =  $5
        WHERE product_id = $6;
        """,
        current_price, product_name, min_price, last_error, is_active, product_id,
    )
