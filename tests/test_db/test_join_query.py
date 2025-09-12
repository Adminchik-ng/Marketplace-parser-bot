import utility_functions
from database import db
import pytest

@pytest.mark.parametrize(
    "products, expected_role, expected_products_count",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            "user",
            3,
        ),
    ]
)
async def test_get_user_active_products(db_pool, products, expected_role, expected_products_count):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        for product in products:
            await utility_functions.add_product_test(
                conn=connection,
                user_id=1,
                product_name=product[0],
                product_url=product[1],
                target_price=product[2],
                marketplace=product[3],
            )

        role, products_count = await db.join_query.get_user_role_and_active_products_count(conn=connection, user_id=1)

    assert role == expected_role
    assert products_count == expected_products_count