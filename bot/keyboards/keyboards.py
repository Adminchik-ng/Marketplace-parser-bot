from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def marketplace_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="🟣 Wildberries", callback_data="marketplace_wildberries")
    builder.button(text="🔴 Ozon", callback_data="marketplace_ozon")
    builder.button(text="🟡 Яндекс.Маркет", callback_data="marketplace_yandex")
    builder.button(text="🟢 Joom", callback_data="marketplace_joom")
    builder.button(text="✖️ Отмена", callback_data="cancel")

    builder.adjust(2)  # row_width=2

    return builder.as_markup()
