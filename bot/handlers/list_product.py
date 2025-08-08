from aiogram import Router, types
from aiogram.filters import Command
from psycopg import AsyncConnection
from database import db

list_router = Router()

@list_router.message(Command(commands=["list"]))
async def cmd_list_products(message: types.Message, conn: AsyncConnection):
    user_id = message.from_user.id

    try:
        products = await db.products.get_user_active_products(conn, user_id=user_id)
    except Exception:
        await message.answer("❌ К сожалению при отслеживании товара  возникли проблемы😞.")
        return

    if not products:
        await message.answer("❌ У вас нет отслеживаемых товаров.")
        return

    # Формируем сообщение с товарами
    lines = [f"📋 Ваши товары ({len(products)}):"]
    for idx, (_, product_name, product_url, target_price) in enumerate(products, start=1):
        # Пример вывода:
        # 1. [Wildberries]
        #      🆔 Название товара: Кроссовки Nike
        #      🔗 Ссылка на товар: https://www.wildberries.ru/catalog/12345678/detail.aspx
        #      🎯 Цель: 6 990 ₽
        lines.append(
            f"{idx}. [Wildberries]\n"
            f"🆔 Название товара: {product_name if product_name else 'пока не отследили😔'}\n"
            f"🔗 Ссылка на товар: {product_url}\n"
            f"🎯 Цель: {target_price}"
        )

    await message.answer("\n\n".join(lines))
