from aiogram import Router, types
from aiogram.filters import Command
from psycopg import AsyncConnection
from datetime import datetime
from database import db

summary_router = Router()

@summary_router.message(Command(commands=["summary"]))
async def cmd_summary(message: types.Message, conn: AsyncConnection):
    user_id = message.from_user.id

    try:
        products = await db.products.get_user_active_products_with_prices(conn, user_id=user_id)
    except Exception:
        await message.answer("❌ К сожалению, возникли проблемы при получении данных.")
        return

    if not products:
        await message.answer("❌ У вас нет отслеживаемых товаров.")
        return

    today_str = datetime.now().strftime("%d.%m.%Y")
    lines = [f"📊 Отчет за {today_str}:\n"]

    for idx, (
        product_id,
        product_name,
        product_url,
        target_price,
        current_price,
        min_price,
        marketplace,
    ) in enumerate(products, start=1):
        product_name_display = product_name or "пока не отследили😔"
        
        if current_price:
            if current_price <= target_price:
                status_line = "✅ Цель достигнута!"
                diff_line = ""
            else:
                diff = current_price - target_price
                status_line = ""
                diff_line = f"🎯 До цели: -{diff} ₽ ({target_price} ₽)"

            lines.append(
                f"{idx}. [{marketplace}]\n"
                f"🆔 Название товара: {product_name_display}\n"
                f"{status_line}\n"
                f"💰 Текущая: {current_price} ₽ | 📉 Минимум: {min_price} ₽\n"
                f"{diff_line}"
            )
        else:
            lines.append(
            f"{idx}. [{marketplace}]\n"
            f"🆔 Название товара: {product_name_display}\n"
            f"ℹ️ Данные о цене еще не доступны.\n"
            f"🔗 Ссылка: {product_url}\n"
        )

    report = "\n".join(line for line in lines if line.strip())  # Убираем пустые строки
    await message.answer(report)
