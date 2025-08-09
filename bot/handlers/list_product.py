from aiogram import Router, types
from aiogram.filters import Command
from asyncpg import Connection
from database import db

list_router = Router()

@list_router.message(Command(commands=["list"]))
async def cmd_list_products(message: types.Message, conn: Connection):
    user_id = message.from_user.id

    try:
        products = await db.products.get_user_active_products(conn, user_id=user_id)
    except Exception:
        await message.answer("❌ К сожалению при отслеживании товара возникли проблемы😞.")
        return

    if not products:
        await message.answer("❌ У вас нет отслеживаемых товаров.")
        return

    # Формируем сообщение с товарами
    lines = [f"📋 Ваши товары ({len(products)}):"]
    for idx, product in enumerate(products, start=1):
        # product — кортеж из 4 элементов: (product_id, product_name, product_url, target_price)
        product_name = product[1]
        product_url = product[2]
        target_price = product[3]
        lines.append(
            f"{idx}. [Wildberries]\n"
            f"🆔 Название товара: {product_name if product_name else 'пока не отследили😔'}\n"
            f"🔗 Ссылка на товар: {product_url}\n"
            f"🎯 Цель: {target_price} ₽"
        )

    inactive_products = await db.products.get_user_inactive_products(conn, user_id=user_id)
 
    
    if inactive_products:
        lines.append(f"📋 Неотслеживаемые товары ({len(inactive_products)}):")
        for idx, inactive_product in enumerate(inactive_products, start=1):
            # inactive_product — кортеж из 4 элементов: (product_id, product_name, product_url, target_price)
            product_name = inactive_product[1]
            product_url = inactive_product[2]
            target_price = inactive_product[3]
            lines.append(
                f"{idx}. [Wildberries]\n"
                f"❌ Данный товар был удален из отслеживаемых\n"
                f"🔗 Ссылка на товар: {product_url}\n"
                f"🎯 Цель: {target_price} ₽"
            )

    await message.answer("\n\n".join(lines))
