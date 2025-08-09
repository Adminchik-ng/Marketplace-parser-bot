import logging

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.handlers import (
    admin_router,
    user_router,
    add_product_router,
    remove_product_router,
    list_router,
    summary_router,
    others_router,
)
from bot.middlewares import (
    DataBaseMiddleware,
    UserLoaderMiddleware,
    ShadowBanMiddleware,
    ActivityCounterMiddleware,
)
from bot.locales.ru import RU
from bot.background_tasks.background_tasks import on_startup
from config.config import Config
import bot.db_pool_singleton.db_pool_singleton as global_pool

logger = logging.getLogger(__name__)


async def main(config: Config) -> None:
    logger.info("Starting bot...")

    # Инициализируем хранилище для FSM через Redis
    storage = RedisStorage(
        redis=Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            username=config.redis.username,
        )
    )

    # Инициализируем бота с HTML разметкой по умолчанию
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=storage)

    # Создаём пул соединений asyncpg для PostgreSQL
    db_pool: asyncpg.Pool = await asyncpg.create_pool(
        user=config.db.user,
        password=config.db.password,
        database=config.db.name,
        host=config.db.host,
        port=config.db.port,
        min_size=1,
        max_size=10,
    )
    global_pool.db_pool_global = db_pool

    # Получаем локализацию
    locales = RU

    # Регистрируем функцию для запуска фоновых задач
    dp.startup.register(on_startup)

    # Регистрируем роутеры в нужном порядке
    logger.info("Including routers...")
    dp.include_routers(
        admin_router,
        user_router,
        add_product_router,
        remove_product_router,
        list_router,
        summary_router,
        others_router,
    )

    # Подключаем middleware в правильном порядке
    logger.info("Including middlewares...")
    dp.update.middleware(DataBaseMiddleware())
    dp.update.middleware(UserLoaderMiddleware())
    dp.update.middleware(ShadowBanMiddleware())
    dp.update.middleware(ActivityCounterMiddleware())

    try:
        # Удаляем webhook, если есть
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем поллинг, передаём пул и другие параметры в context
        await dp.start_polling(
            bot,
            db_pool=db_pool,
            locales=locales,
            admin_ids=config.bot.admin_ids,
        )
    except Exception as e:
        logger.exception("Exception occurred while running the bot: %s", e)
    finally:
        # Закрываем пул при завершении
        await db_pool.close()
        logger.info("Connection to Postgres closed")
