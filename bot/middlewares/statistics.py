import logging
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Update, User
from asyncpg import Connection
from database import db  # Ваш модуль с функцией add_user_activity

logger = logging.getLogger(__name__)


class ActivityCounterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user: Optional[User] = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        result = await handler(event, data)

        conn: Optional[Connection] = data.get("conn")
        if conn is None:
            logger.error("No database connection found in middleware data.")
            raise RuntimeError("Missing database connection for activity logging.")

        try:
            await db.activity.add_user_activity(conn, user_id=user.id)
        except Exception as e:
            logger.error(f"Failed to add user activity: {e}", exc_info=True)

        return result
