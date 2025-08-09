import logging
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User
from asyncpg import Connection
from database import db

logger = logging.getLogger(__name__)


class UserLoaderMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user: Optional[User] = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        conn: Optional[Connection] = data.get("conn")
        if conn is None:
            logger.error("Database connection not found in middleware data.")
            raise RuntimeError("Missing database connection for user loading.")

        user_row = await db.users.get_user(conn, telegram_id=user.id)
        if user_row is None:
            logger.warning("User not found in DB: %d", user.id)
            return await handler(event, data)

        data["user_row"] = user_row

        return await handler(event, data)
