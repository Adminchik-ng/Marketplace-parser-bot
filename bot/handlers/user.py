import logging
from contextlib import suppress

from aiogram import Bot, Router
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import KICKED, ChatMemberUpdatedFilter, Command, CommandStart
from aiogram.types import BotCommandScopeChat, ChatMemberUpdated, Message
from bot.enums.roles import UserRole
from bot.keyboards.menu_button import get_main_menu_commands
from database import db
from psycopg.connection_async import AsyncConnection

logger = logging.getLogger(__name__)

# Инициализируем роутер уровня модуля
user_router = Router()


# Этот хэндлер срабатывает на команду /start
@user_router.message(CommandStart())
async def process_start_command(
    message: Message, 
    conn: AsyncConnection, 
    bot: Bot, 
    locales: dict[str, str], 
    admin_ids: list[int],
):
    user_row = await db.users.get_user(conn, telegram_id=message.from_user.id)
    if user_row is None:
        if message.from_user.id in admin_ids:
            user_role = UserRole.ADMIN
        else:
            user_role = UserRole.USER

        await db.users.add_user(
            conn,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            language=message.from_user.language_code,
            role=user_role
        )
    else:
        user_role = UserRole(user_row.role)
        await db.users.change_user_alive_status(
            conn, 
            is_alive=True, 
            telegram_id=message.from_user.id, 
        )
    
    await bot.set_my_commands(
        commands=get_main_menu_commands(locales=locales, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT,
            chat_id=message.from_user.id
        )
    )

    await message.answer(text=locales.get("/start"))


# Этот хэндлер срабатывает на команду /help
@user_router.message(Command(commands="help"))
async def process_help_command(message: Message, locales: dict[str, str]):
    await message.answer(text=locales.get("/help"))


# Этот хэндлер будет срабатывать на блокировку бота пользователем
@user_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, conn: AsyncConnection):
    logger.info("User %d has blocked the bot", event.from_user.id)
    await db.users.change_user_alive_status(conn, telegram_id=event.from_user.id, is_alive=False)