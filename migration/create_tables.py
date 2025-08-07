import asyncio
import os
import sys
import logging

from psycopg import AsyncConnection, Error
from database.connection import get_pg_connection
from config.config import Config, load_config

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format,
)
logger = logging.getLogger(__name__)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    connection: AsyncConnection | None = None

    try:
        connection = await get_pg_connection(
            db_name=config.db.name,
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
        )
        async with connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    # Таблица пользователей
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id BIGSERIAL PRIMARY KEY,
                            telegram_id BIGINT UNIQUE NOT NULL,
                            username VARCHAR(64),
                            language VARCHAR(8),
                            role VARCHAR(16) DEFAULT 'user',
                            is_alive BOOLEAN DEFAULT TRUE,
                            banned BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMPTZ DEFAULT now(),
                            updated_at TIMESTAMPTZ DEFAULT now()
                        );
                    """)

                    # Таблица активности
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS activity (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
                            actions INT NOT NULL DEFAULT 1
                        );
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_user_day
                        ON activity (user_id, activity_date);
                    """)

                    # Таблица товаров
                    await cursor.execute("""
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
                logger.info("Tables `users`, `activity`, and `products` were successfully created")
    except Error as db_error:
        logger.exception("Database-specific error: %s", db_error)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.info("Connection to Postgres closed")

if __name__ == "__main__":
    asyncio.run(main())
