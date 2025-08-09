import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update
from asyncpg.pool import Pool  # если у вас пул от asyncpg
from bot.locales.ru import RU

logger = logging.getLogger(__name__)


class DataBaseMiddleware(BaseMiddleware):
    """
    Middleware для передачи подключения к базе данных (asyncpg.Pool) и языковых констант в контекст хэндлера.
    Открывает транзакцию на время обработки update.
    """

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        db_pool: Pool | None = data.get("db_pool")

        if db_pool is None:
            logger.error("Database pool is not provided in middleware data.")
            raise RuntimeError("Missing db_pool in middleware context.")

        # Создаём соединение из пула
        async with db_pool.acquire() as connection:
            # Открываем транзакцию
            async with connection.transaction():
                # Добавляем в контекст хэндлера соединение и локализацию
                data["conn"] = connection
                data["locales"] = RU

                try:
                    result = await handler(event, data)
                except Exception as e:
                    logger.exception("Transaction rolled back due to error: %s", e)
                    raise

        # Здесь можно добавить post-transaction код при необходимости

        return result
