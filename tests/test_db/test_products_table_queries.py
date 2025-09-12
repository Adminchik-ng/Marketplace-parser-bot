import utility_functions
from database import db
import pytest

@pytest.mark.parametrize(
    "user_id, marketplace, product_url, target_price",
    [
        (1, "Мarket1", "http://example.com/product1", 100),
        (2, "Мarket2", "http://example.com/product2", 200),
        (3, "Мarket3", "http://example.com/product3", 300),
    ]
)
async def test_add_product(db_pool, user_id, marketplace, product_url, target_price):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection, telegram_id=user_id)
        await db.products.add_product(
            conn=connection,
            user_id=user_id,
            marketplace=marketplace,
            product_url=product_url,
            target_price=target_price,
        )

        row = await utility_functions.get_product_by_user_id_test(conn=connection, user_id=user_id)
        assert row is not None
        assert row["user_id"] == user_id
        assert row["marketplace"] == marketplace
        assert row["product_url"] == product_url
        assert row["target_price"] == target_price
        
        
@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            3,
        ),
    ]
)
async def test_get_user_active_products(db_pool, products, expected_distribution):
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

        row = await db.products.get_user_active_products(conn=connection, user_id=1)

    assert row is not None
    assert len(row) == expected_distribution
    assert all(elem in row[0] for elem in products[0]) 
    assert all(elem in row[1] for elem in products[1]) 
    assert all(elem in row[2] for elem in products[2]) 
    
    


@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            3,
        ),
    ]
)
async def test_get_user_inactive_products(db_pool, products, expected_distribution):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        for product in products:
            await utility_functions.add_product_test(
                conn=connection,
                user_id=1,
                product_name=product[0],
                product_url=product[1],
                target_price=product[2],
                is_active=False,
                marketplace=product[3],
            )

        row = await db.products.get_user_inactive_products(conn=connection, user_id=1)

    assert row is not None
    assert len(row) == expected_distribution
    assert all(elem in row[0] for elem in products[0]) 
    assert all(elem in row[1] for elem in products[1]) 
    assert all(elem in row[2] for elem in products[2])     
    

@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            3,
        ),
    ]
)
async def test_get_user_inactive_products_to_turn_on_after_block_bot(db_pool, products, expected_distribution):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        for product in products:
            await utility_functions.add_product_test(
                conn=connection,
                user_id=1,
                product_name=product[0],
                product_url=product[1],
                target_price=product[2],
                is_active=False,
                marketplace=product[3],
            )

        row = await db.products.get_user_inactive_products_to_turn_on_after_block_bot(conn=connection, user_id=1)

    assert row is not None
    assert len(row) == expected_distribution
    assert row[0] == 1 # product_id = 1 т.к. данные во всех таблицах стираются каждый тест, индексы обнуляются
    assert row[1] == 2
    assert row[2] == 3  


@pytest.mark.parametrize(
    "product_name, product_url, target_price, marketplace",
    [
        ("product1", "http://example.com/product1", 100, "Market1"),
        ("product2", "http://example.com/product2", 200, "Market2"),
        ("product3", "http://example.com/product3", 300, "Market3"),
    ]
)
async def test_get_product_by_id_and_user(db_pool, product_name, product_url, target_price, marketplace):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        await utility_functions.add_product_test(
            conn=connection,
            user_id=1,
            product_name=product_name,
            marketplace=marketplace,
            product_url=product_url,
            target_price=target_price,
        )

        product_name_check, product_url_check = await db.products.get_product_by_id_and_user(conn=connection, user_id=1, product_id=1) # product_id = 1 т.к. данные во всех таблицах стираются каждый тест, индексы обнуляются
        assert product_name_check == product_name
        assert product_url_check == product_url
        
        
@pytest.mark.parametrize(
    "product_name, product_url, target_price, marketplace",
    [
        ("product1", "http://example.com/product1", 100, "Market1"),
        ("product2", "http://example.com/product2", 200, "Market2"),
        ("product3", "http://example.com/product3", 300, "Market3"),
    ]
)
async def test_delete_product_by_id(db_pool, product_name, product_url, target_price, marketplace):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        await utility_functions.add_product_test(
            conn=connection,
            user_id=1,
            product_name=product_name,
            marketplace=marketplace,
            product_url=product_url,
            target_price=target_price,
        )
        await db.products.delete_product_by_id(conn=connection, product_id=1) # product_id = 1 т.к. данные во всех таблицах стираются каждый тест, индексы обнуляются
        
        products_count = await utility_functions.get_products_count_test(conn=connection)
        
        assert products_count == 0
        


@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            3,
        ),
    ]
)
async def test_get_user_products_with_details(db_pool, products, expected_distribution):
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

        row = await db.products.get_user_products_with_details(conn=connection, user_id=1)

    assert row is not None
    assert len(row) == expected_distribution
    assert all(elem in row[0] for elem in products[0]) 
    assert all(elem in row[1] for elem in products[1]) 
    assert all(elem in row[2] for elem in products[2]) 


@pytest.mark.parametrize(
    "product_name, product_url, target_price, marketplace, is_active",
    [
        ("product1", "http://example.com/product1", 100, "Market1", True),
        ("product2", "http://example.com/product2", 200, "Market2", False),
        ("product3", "http://example.com/product3", 300, "Market3", True),
    ]
)
async def test_change_product_active_status(db_pool, product_name, product_url, target_price, marketplace, is_active):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        await utility_functions.add_product_test(
            conn=connection,
            user_id=1,
            product_name=product_name,
            marketplace=marketplace,
            product_url=product_url,
            is_active=is_active,
            target_price=target_price,
        )

        await db.products.change_product_active_status(conn=connection, is_active=(not is_active), product_id=1) # product_id = 1 т.к. данные во всех таблицах стираются каждый тест, индексы обнуляются
        
        active_status_check = await utility_functions.get_product_active_status_id_test(conn=connection, user_id=1)
            
        assert active_status_check == (not is_active)


@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            3,
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_products_items_for_parsing(db_pool, products, expected_distribution):
    async with db_pool.acquire() as connection:
        # Добавляем пользователя с user_id=1 по умолчанию
        await utility_functions.add_user_test_default_test(conn=connection)
        
        # Добавляем все продукты из параметров
        for product in products:
            await utility_functions.add_product_test(
                conn=connection,
                user_id=1,
                product_name=product[0],
                product_url=product[1],
                target_price=product[2],
                marketplace=product[3],
            )

        # Запрашиваем продукты для парсинга
        rows = await db.products.get_products_items_for_parsing(conn=connection)

    assert rows is not None
    assert len(rows) == expected_distribution

    # Проверяем соответствие каждого продукта по нужным полям
    for expected_product, actual_row in zip(products, rows):
        _, expected_url, expected_price, expected_marketplace = expected_product
        
        actual_user_id = actual_row[0]      # user_id
        actual_product_url = actual_row[2]  # product_url
        actual_marketplace = actual_row[3]  # marketplace
        actual_min_price = actual_row[4]    # min_price
        actual_target_price = actual_row[5] # target_price
        
        assert actual_user_id == 1
        assert expected_url == actual_product_url
        assert expected_marketplace == actual_marketplace
        assert actual_min_price == None
        assert expected_price == actual_target_price
        

@pytest.mark.parametrize(
    "product_name, product_url, target_price, marketplace, is_active, current_price, updated_product_name, min_price, last_error, updated_is_active",
    [
        ("product1", "http://example.com/product1", 100, "Market1", True, 200, "updated_product1", 150, None, True),
        ("product2", "http://example.com/product2", 200, "Market2", False, 300, "updated_product2", 300, 'error', False),
        ("product3", "http://example.com/product3", 300, "Market3", True,  200, "updated_product3", 190, None, True),
    ]
)
async def test_change_product_details_after_parsing(db_pool, product_name, product_url, target_price, marketplace, is_active, current_price, updated_product_name, min_price, last_error, updated_is_active):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        await utility_functions.add_product_test(
            conn=connection,
            user_id=1,
            product_name=product_name,
            marketplace=marketplace,
            product_url=product_url,
            is_active=is_active,
            target_price=target_price,
        )

        await db.products.change_product_details_after_parsing(
            conn=connection, 
            product_id=1,  # product_id = 1 т.к. данные во всех таблицах стираются каждый тест, индексы обнуляются
            current_price=current_price, 
            product_name=updated_product_name, 
            min_price=min_price, 
            last_error=last_error, 
            is_active=updated_is_active
            )
        
        row = await utility_functions.get_product_after_parsing_test(conn=connection, user_id=1)
            
        assert row['current_price'] == current_price
        assert row['product_name'] == updated_product_name
        assert row['min_price'] == min_price
        assert row['last_error'] == last_error
        assert row['is_active'] == updated_is_active
        

@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            [
              ("Market1", 1),
              ("Market2", 1),
              ("Market3", 1),  
            ],
        ),
    ]
)
async def test_get_active_products_by_marketplace(db_pool, products, expected_distribution):
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

        row = await db.products.get_active_products_by_marketplace(conn=connection)

    assert row is not None
    assert all(elem in row for elem in expected_distribution) 


@pytest.mark.parametrize(
    "products, expected_distribution",
    [
        (
            [
                ("product1", "http://example.com/product1", 100, "Market1"),
                ("product2", "http://example.com/product2", 200, "Market2"),
                ("product3", "http://example.com/product3", 300, "Market3")    
            ],
            [
              ("Market1", 1),
              ("Market2", 1),
              ("Market3", 1),  
            ],
        ),
    ]
)
async def test_get_inactive_products_by_marketplace(db_pool, products, expected_distribution):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test_default_test(conn=connection) # user_id = 1 по умолчанию
        for product in products:
            await utility_functions.add_product_test(
                conn=connection,
                user_id=1,
                product_name=product[0],
                product_url=product[1],
                target_price=product[2],
                last_error='error', 
                marketplace=product[3],
            )

        row = await db.products.get_inactive_products_by_marketplace(conn=connection)

    assert row is not None
    assert all(elem in row for elem in expected_distribution)     