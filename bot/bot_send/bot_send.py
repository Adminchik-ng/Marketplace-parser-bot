from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

async def send_message(bot: Bot, *, chat_id: int, current_price: int, product_name: str, target_price: int, url: str) -> None:
    # safe_product_name = escape_markdown(product_name)
    # Не экранируем URL, передаем как есть
    logger.info(f"Sending message to chat {chat_id}")
    message = (
        "🎉 *Отличные новости!*\n\n"
        "⬇️ Cнизилась цена на товар:\n"
        f"🆔 *{product_name}*\n"
        f"➡️ И теперь составляет: *{current_price} руб.*\n"
        f"🎯 Ваш целевой порог: *{target_price} руб.*\n\n"
        "⏳ Поторопитесь, пока действует выгодное предложение!\n\n"
        f"🔗 Ссылка: [перейти к товару]({url})"
    )
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")


