import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from bot.enums.roles import UserRole
from bot.filters.filters import UserRoleFilter
from database import db
from asyncpg import Connection  # заменено на asyncpg

logger = logging.getLogger(__name__)
admin_router = Router()

admin_router.message.filter(UserRoleFilter(UserRole.ADMIN))


@admin_router.message(Command('help'))
async def process_admin_help_command(message: Message, locales: dict):
    await message.answer(text=locales.get('/help_admin'))


@admin_router.message(Command('statistics'))
async def process_admin_statistics_command(
    message: Message, 
    conn: Connection, 
    locales: dict[str, str]
):
    total_users = await db.users.get_total_users(conn)
    active_today = await db.activity.get_active_users_today(conn)
    roles_dist = await db.users.get_users_role_distribution(conn)
    new_users_percent = await db.users.get_percent_new_users_week(conn)
    active_products = await db.products.get_active_products_by_marketplace(conn)
    inactive_products = await db.products.get_inactive_products_by_marketplace(conn)
    top_users = await db.activity.get_statistics(conn)  # топ пользователей по активности
    
    if not any([total_users, active_today, roles_dist, new_users_percent, active_products, inactive_products, top_users]):
        await message.answer(text=locales.get("no_statistics", "Статистика отсутствует."))
        return

    lines = []
    lines.append("📊 Статистика бота 📊")
    lines.append("────────────────────")
    if total_users is not None:
        lines.append(f"👥 Всего пользователей: {total_users}")
    if active_today is not None:
        lines.append(f"🔥 Активных сегодня: {active_today}")
    if roles_dist:
        lines.append("🛡️ Распределение по ролям:")
        for role, banned, count in roles_dist:
            status_emoji = "🚫" if banned else "✅"
            status_text = "заблокирован" if banned else "активен"
            lines.append(f"  - {role.capitalize()} {status_emoji} ({status_text}): {count}")
    if new_users_percent is not None:
        lines.append(f"🆕 Новых за неделю: {new_users_percent:.2f}%")
    if active_products:
        lines.append("📦 Активные товары по маркетплейсам:")
        for marketplace, count in active_products:
            lines.append(f"  - 🏷️ {marketplace}: {count}")
    if inactive_products:
        lines.append("📦 Неактивные товары по маркетплейсам:")
        for marketplace, count in inactive_products:
            lines.append(f"  - 🏷️ {marketplace}: {count}")
    if top_users:
        lines.append("🏆 Топ пользователей по активности:")
        for i, (user_id, actions) in enumerate(top_users, 1):
            lines.append(f"  {i}. 👤 User ID {user_id}: {actions} действий")

    final_text = "\n".join(lines)
    await message.answer(text=final_text)




@admin_router.message(Command("ban"))
async def process_ban_command(
    message: Message, 
    command: CommandObject, 
    conn: Connection, 
    locales: dict[str, str]
) -> None:
    args = command.args

    if not args:
        await message.reply(locales.get('empty_ban_answer'))
        return

    arg_user = args.split()[0].strip()

    if arg_user.isdigit():
        banned_status = await db.users.get_user_banned_status_by_id(conn, user_id=int(arg_user))
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
        # Изменяем статус
        if arg_user.isdigit():
            await db.users.change_user_banned_status_by_id(conn, user_id=int(arg_user), banned=True)
        else:
            await db.users.change_user_banned_status_by_username(conn, username=arg_user[1:], banned=True)
        await message.reply(text=locales.get('successfully_banned'))


@admin_router.message(Command('unban'))
async def process_unban_command(
    message: Message, 
    command: CommandObject, 
    conn: Connection, 
    locales: dict[str, str]
) -> None:
    args = command.args

    if not args:
        await message.reply(locales.get('empty_unban_answer'))
        return

    arg_user = args.split()[0].strip()

    if arg_user.isdigit():
        banned_status = await db.users.get_user_banned_status_by_id(conn, user_id=int(arg_user))
    elif arg_user.startswith('@'):
        banned_status = await db.users.get_user_banned_status_by_username(conn, username=arg_user[1:])
    else:
        await message.reply(text=locales.get('incorrect_unban_arg'))
        return

    if banned_status is None:
        await message.reply(locales.get('no_user'))
    elif banned_status:
        if arg_user.isdigit():
            await db.users.change_user_banned_status_by_id(conn, user_id=int(arg_user), banned=False)
        else:
            await db.users.change_user_banned_status_by_username(conn, username=arg_user[1:], banned=False)
        await message.reply(text=locales.get('successfully_unbanned'))
    else:
        await message.reply(locales.get('not_banned'))
