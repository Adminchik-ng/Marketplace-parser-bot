import logging
from contextlib import suppress
from typing import Optional

from aiogram import Bot, Router
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import KICKED, ChatMemberUpdatedFilter, Command, CommandStart
from aiogram.types import BotCommandScopeChat, ChatMemberUpdated, Message
from asyncpg import Connection

from bot.enums.roles import UserRole
from bot.keyboards.menu_button import get_main_menu_commands
from database import db


logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def process_start_command(
    message: Message,
    conn: Connection,
    bot: Bot,
    locales: dict[str, str],
    admin_ids: list[int],
    user_row: Optional[object] = None,
):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_row is None:
        if user_id in admin_ids:
            user_role = UserRole.ADMIN
        else:
            user_role = UserRole.USER

        await db.users.add_user(
            conn=conn,
            telegram_id=user_id,
            chat_id=chat_id,
            username=message.from_user.username,
            language=message.from_user.language_code or "ru",
            role=user_role.value if hasattr(user_role, "value") else user_role,
        )
    else:
        user_role = UserRole(user_row.role)
        await db.users.change_user_alive_status(
            conn=conn,
            is_alive=True,
            telegram_id=user_id,
        )

        products = await db.products.get_user_inactive_products_to_turn_on_after_block_bot(conn=conn, user_id=user_id)
        if products:
            for product_id in products:
                await db.products.change_product_active_status(conn=conn, is_active=True, product_id=product_id)

    await bot.set_my_commands(
        commands=get_main_menu_commands(locales=locales, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT,
            chat_id=user_id,
        )
    )

    await message.answer(text=locales.get("/start"))


@user_router.message(Command(commands="help"))
async def process_help_command(message: Message, locales: dict[str, str]):
    await message.answer(text=locales.get("/help"))

@user_router.message(Command(commands="info"))
async def process_help_command(message: Message, locales: dict[str, str]):
    await message.answer(text=locales.get("/info"))


@user_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, conn: Connection):
    user_id = event.from_user.id
    logger.info("User %d has blocked the bot", user_id)

    await db.users.change_user_alive_status(conn=conn, telegram_id=user_id, is_alive=False)

    try:
        products = await db.products.get_user_active_products(conn=conn, user_id=user_id)
    except Exception:
        return

    if not products:
        return

    for product_id, _, _, _, _ in products:
        await db.products.change_product_active_status(conn=conn, is_active=False, product_id=product_id)
