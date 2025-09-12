import pytest_asyncio
import asyncpg
from config.config import Config, load_config


@pytest_asyncio.fixture(scope='package')
async def db_pool():
    config: Config = load_config(".env.test")
    pool = await asyncpg.create_pool(
        user=config.db.user,
        password=config.db.password,
        database=config.db.name,
        host=config.db.host,
        port=config.db.port,
        min_size=1,
        max_size=10,
    )
    yield pool
    await pool.close()

@pytest_asyncio.fixture(autouse=True, scope='package')
async def setup_db(db_pool):
    async with db_pool.acquire() as connection:
        try:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    chat_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(64),
                    language VARCHAR(8),
                    role VARCHAR(16) DEFAULT 'user',
                    is_alive BOOLEAN DEFAULT TRUE,
                    banned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                );
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS activity (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    actions INT NOT NULL DEFAULT 1
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_user_day ON activity (user_id, activity_date);
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                    marketplace VARCHAR(32) NOT NULL,
                    product_name VARCHAR(255),
                    product_url TEXT NOT NULL,
                    target_price INTEGER NOT NULL CHECK (target_price > 0),
                    current_price INTEGER,
                    min_price INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_checked TIMESTAMPTZ,
                    last_error TEXT,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                );
            """)
            yield  # После yield идут тесты
        finally:
            await connection.execute("DROP TABLE IF EXISTS products CASCADE;")
            await connection.execute("DROP TABLE IF EXISTS activity CASCADE;")
            await connection.execute("DROP TABLE IF EXISTS users CASCADE;")

import pytest

@pytest_asyncio.fixture(scope='function', autouse=True) # попробовать поставить параметр moodle так как изменился состав проекта
async def clean_users_table(db_pool):
    async with db_pool.acquire() as conn:
        # Очистка таблиц до теста
        await conn.execute("TRUNCATE TABLE users, activity, products RESTART IDENTITY CASCADE;")
        yield
        # Очистка таблиц после теста
        await conn.execute("TRUNCATE TABLE users, activity, products RESTART IDENTITY CASCADE;")
