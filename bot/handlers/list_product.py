from aiogram import Router, types
from aiogram.filters import Command
from asyncpg import Connection
from database import db

list_router = Router()
MAX_MSG_LENGTH = 4096


async def send_long_message(message_obj: types.Message, text: str):
    """
    Отправляет длинное сообщение частями по лимиту Telegram (4096 символов),
    разбивая по последнему переносу строки.
    """
    while text:
        part = text[:MAX_MSG_LENGTH]
        cut_pos = part.rfind("\n")
        if cut_pos != -1 and len(text) > MAX_MSG_LENGTH:
            part = part[:cut_pos]

        await message_obj.answer(part, parse_mode="Markdown")
        text = text[len(part):]


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

    lines = [f"📋 Ваши товары ({len(products)}):"]
    for idx, product in enumerate(products, start=1):
        # product — кортеж: (product_id, product_name, product_url, target_price, marketplace)
        product_name = product[1]
        product_url = product[2]
        target_price = product[3]
        marketplace = product[4]

        if product_name:
            lines.append(
                f"{idx}. [{marketplace.title()}]\n"
                f"🆔 Название товара: {product_name}\n"
                f"🔗 Ссылка на товар: [перейти к товару]({product_url})\n"
                f"🎯 Цель: {target_price} ₽"
            )
        else:
            lines.append(
                f"{idx}. [{marketplace.title()}]\n"
                f"⌛ Информация по товару пока недоступна, но мы уже работаем над её получением!\n"
                f"🔗 Ссылка на товар: [перейти к товару]({product_url})\n"
                f"🎯 Цель: {target_price} ₽"
            )

    inactive_products = await db.products.get_user_inactive_products(conn, user_id=user_id)

    if inactive_products:
        lines.append(f"⛔ Неотслеживаемые товары ({len(inactive_products)}):")
        for idx, inactive_product in enumerate(inactive_products, start=1):
            product_name = inactive_product[1]
            product_url = inactive_product[2]
            target_price = inactive_product[3]
            marketplace = inactive_product[4]

            lines.append(
                f"{idx}. [{marketplace.title()}]\n"
                f"❌ Данный товар был удален из отслеживаемых\n"
                f"🔗 Ссылка на товар: [перейти к товару]({product_url})\n"
                f"🎯 Цель: {target_price} ₽"
            )

    report = "\n\n".join(lines)

    await send_long_message(message, report)
