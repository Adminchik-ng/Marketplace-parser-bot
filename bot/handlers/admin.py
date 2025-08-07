import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from bot.enums.roles import UserRole
from bot.filters.filters import UserRoleFilter
from database import db
from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

admin_router = Router()

admin_router.message.filter(UserRoleFilter(UserRole.ADMIN,))


# Этот хэндлер будет срабатывать на команду /help для пользователя с ролью `UserRole.ADMIN`
@admin_router.message(Command('help'))
async def process_admin_help_command(message: Message, locales: dict):
    await message.answer(text=locales.get('/help_admin'))


# Этот хэндлер будет срабатывать на команду /statistics для пользователя с ролью `UserRole.ADMIN`
@admin_router.message(Command('statistics'))
async def process_admin_statistics_command(message: Message, conn: AsyncConnection, locales: dict[str, str]):
    statistics = await db.activity.get_statistics(conn)
    await message.answer(
        text=locales.get("statistics").format(
            "\n".join(
                f"{i}. <b>{stat[0]}</b>: {stat[1]}"
                for i, stat in enumerate(statistics, 1)
            )
        )
    )


# Этот хэндлер будет срабатывать на команду /ban для пользователя с ролью `UserRole.ADMIN`
@admin_router.message(Command("ban"))
async def process_ban_command(
    message: Message, 
    command: CommandObject, 
    conn: AsyncConnection, 
    locales: dict[str, str]
) -> None:
    args = command.args

    if not args:
        await message.reply(locales.get('empty_ban_answer'))
        return
    
    arg_user = args.split()[0].strip()
    
    if arg_user.isdigit():
        banned_status = await db.users.get_user_banned_status_by_id(conn, telegram_id=int(arg_user))
    elif arg_user.startswith('@'):
        banned_status = await db.users.get_user_banned_status_by_username(conn, username=arg_user[1:])
    else:
        await message.reply(text=locales.get('incorrect_ban_arg'))
        return
    
    if banned_status is None:
        await message.reply(locales.get('no_user'))
    elif banned_status:
        await message.reply(locales.get('already_banned'))
    else:
        if arg_user.isdigit():
            await db.users.change_user_banned_status_by_id(conn, telegram_id=int(arg_user), banned=True)
        else:
            await db.users.change_user_banned_status_by_username(conn, username=arg_user[1:], banned=True)
        await message.reply(text=locales.get('successfully_banned'))


# Этот хэндлер будет срабатывать на команду /unban для пользователя с ролью `UserRole.ADMIN`
@admin_router.message(Command('unban'))
async def process_unban_command(
    message: Message, 
    command: CommandObject, 
    conn: AsyncConnection, 
    locales: dict[str, str]
) -> None:
    args = command.args

    if not args:
        await message.reply(locales.get('empty_unban_answer'))
        return
    
    arg_user = args.split()[0].strip()
    
    if arg_user.isdigit():
        banned_status = await db.users.get_user_banned_status_by_id(conn, telegram_id=int(arg_user))
    elif arg_user.startswith('@'):
        banned_status = await db.users.get_user_banned_status_by_username(conn, username=arg_user[1:])
    else:
        await message.reply(text=locales.get('incorrect_unban_arg'))
        return
    
    if banned_status is None:
        await message.reply(locales.get('no_user'))
    elif banned_status:
        if arg_user.isdigit():
            await db.users.change_user_banned_status_by_id(conn, telegram_id=int(arg_user), banned=False)
        else:
            await db.users.change_user_banned_status_by_username(conn, username=arg_user[1:], banned=False)
        await message.reply(text=locales.get('successfully_unbanned'))
    else:
        await message.reply(locales.get('not_banned'))