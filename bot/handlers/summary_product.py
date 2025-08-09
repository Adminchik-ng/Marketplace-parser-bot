from datetime import datetime
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command
from asyncpg import Connection
from datetime import timedelta

from database import db


summary_router = Router()


@summary_router.message(Command(commands=["summary"]))
async def cmd_summary(message: types.Message, conn):
    user_id = message.from_user.id

    try:
        # Предполагается, что метод возвращает данные с last_checked включительно
        products = await db.products.get_user_active_products_with_prices_and_errors(
            conn, user_id=user_id
        )
    except Exception:
        await message.answer("❌ К сожалению, возникли проблемы при получении данных.")
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
            last_checked,  # Добавьте это поле в ваш SQL-запрос
        ) = item
        if isinstance(last_checked, datetime):
                # Переводим last_checked в Москву
            last_checked_moscow = last_checked + timedelta(hours=3)
            last_checked_str = last_checked_moscow.strftime("%d.%m.%Y %H:%M")
        else:
            last_checked_str = str(last_checked) if last_checked else "еще не проверяли😔"

        if last_error:
            
            lines.append(
                f"{idx}. ❌[{marketplace}]❌\n"
                f"⚠️ Отслеживание прервано из-за ошибки: "
                f"{last_error}\n"
                f"🕒 Последняя проверка: {last_checked_str}\n"
                f"🔗 Ссылка: {product_url}\n"
                f"⚠️ Внимание! Товар убран из отслеживания.\n"
            )
            continue

        product_name_display = product_name or "пока не отследили😔"

        if current_price is not None:
            if current_price <= target_price:
                status_line = "✅ Цель достигнута!"
                diff_line = "\n"
            else:
                diff = current_price - target_price
                status_line = ""
                diff_line = f"\n❌ До цели: {diff} ₽ ({target_price} ₽)\n"

            lines.append(
                f"{idx}. [{marketplace}]\n"
                f"🆔 Название товара: {product_name_display}\n"
                 f"🔗 Ссылка: {product_url}\n"
                f"{status_line}"
                f"🎯 Целевая цена: {target_price} ₽\n"
                f"💰 Текущая: {current_price} ₽ | 📉 Минимум: {min_price} ₽"
                f"{diff_line}"
                f"🕒 Последняя проверка: {last_checked_str}\n"
            )
        else:
            lines.append(
                f"{idx}. [{marketplace}]\n"
                f"🆔 Название товара: {product_name_display}\n"
                f"🔗 Ссылка: {product_url}\n"
                f"ℹ️ Данные о цене еще не доступны.\n"
                f"🔗 Ссылка: {product_url}\n"
                f"🕒 Последняя проверка: {last_checked_str}\n"
            )

    report = "\n".join(line for line in lines if line.strip())

    await message.answer(report)