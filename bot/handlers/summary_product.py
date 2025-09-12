from datetime import datetime, timedelta
from math import log
from aiogram import Router, types
from aiogram.filters import Command

from database import db

import logging

logger = logging.getLogger(__name__)

summary_router = Router()
MAX_MSG_LENGTH = 4096


async def send_long_message(message_obj: types.Message, text: str):
    """
    Функция для отправки длинного текста частями по лимиту Telegram (4096 символов),
    разбивая по последнему переносу строки, чтобы не обрезать слова.
    """
    while text:
        part = text[:MAX_MSG_LENGTH]

        # Разбиваем по последнему \n, если это возможно и сообщение длиннее лимита
        cut_pos = part.rfind("\n")
        if cut_pos != -1 and len(text) > MAX_MSG_LENGTH:
            part = part[:cut_pos]

        await message_obj.answer(part, parse_mode="Markdown")
        text = text[len(part):]


@summary_router.message(Command(commands=["summary"]))
async def cmd_summary(message: types.Message, conn):
    user_id = message.from_user.id

    try:
        products = await db.products.get_user_products_with_details(
            conn, user_id=user_id
        )
    except Exception:
        await message.answer("❌ К сожалению, возникли проблемы при получении данных.")
        logger.error("Failed to get user products with details.", exc_info=True) 
        return

    if not products:
        await message.answer("❌ У вас нет отслеживаемых товаров.")
        return

    today_str = datetime.now().strftime("%d.%m.%Y")
    lines = [f"📊 Отчет за {today_str}:\n"]

    for idx, item in enumerate(products, start=1):
        (
            product_id,
            product_name,
            product_url,
            target_price,
            current_price,
            min_price,
            marketplace,
            last_error,
            last_checked,
        ) = item

        if isinstance(last_checked, datetime):
            last_checked_moscow = last_checked + timedelta(hours=3)
            last_checked_str = last_checked_moscow.strftime("%d.%m.%Y %H:%M")
        else:
            last_checked_str = str(last_checked) if last_checked else None

        if last_error:
            lines.append(
                f"{idx}. ❌[{marketplace.title()}]❌\n"
                f"⚠️ Отслеживание прервано из-за ошибки: {last_error}\n"
                f"🕒 Последняя проверка: {last_checked_str}\n"
                f"🔗 Ссылка: [перейти к товару]({product_url})\n"
                f"❗️ Внимание! Товар убран из отслеживания.\n"
            )
            continue

        if current_price is not None:
            if current_price <= target_price:
                status_line = "✅ Цель достигнута!\n"
                diff_line = "\n"
            else:
                diff = current_price - target_price
                status_line = ""
                diff_line = f"\n🔻 До цели: {diff} ₽\n"

            lines.append(
                f"{idx}. [{marketplace.title()}]\n"
                f"{status_line}"
                f"🆔 Название товара: {product_name}\n"
                f"🔗 Ссылка: [перейти к товару]({product_url})\n"
                f"🎯 Целевая цена: {target_price} ₽\n"
                f"💰 Текущая: {current_price} ₽"
                f"{diff_line}"
                f"📉 Минимум: {min_price} ₽\n"
                f"🕒 Последняя проверка: {last_checked_str}\n"
            )
        else:
            lines.append(
                f"{idx}. [{marketplace.title()}]\n"
                f"⌛ Информация по товару пока недоступна, но мы уже работаем над её получением!\n"
                f"🔗 Ссылка: [перейти к товару]({product_url})\n"
                f"🎯 Целевая цена: {target_price} ₽\n"
            )

    report = "\n".join(line for line in lines if line.strip())

    await send_long_message(message, report)
