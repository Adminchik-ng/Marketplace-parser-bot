from aiogram import Router
from aiogram.types import Message

others_router = Router()

@others_router.message()
async def unknown_message_handler(message: Message):
    # Можно взять сообщение из i18n для мультиязычности, если есть, или заменить на своё
    text = (
    "🤔 Я не совсем понял, что вы хотите.\n"
    "Попробуйте использовать команду /help для списка доступных команд."
)

    await message.answer(text=text)
