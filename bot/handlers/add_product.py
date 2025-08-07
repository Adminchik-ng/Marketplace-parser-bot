import re
from contextlib import suppress

from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from psycopg import AsyncConnection

from ..states.states import AddProductStates
from ..keyboards.keyboards import marketplace_keyboard

add_product_router = Router()

VALID_MARKETPLACES = {"wildberries", "ozon", "yandex", "joom"}

URL_REGEX = re.compile(
    r'^https?://(?:www\.)?'
    r'('
    r'wildberries\.ru|'               # Wildberries
    r'ozon\.ru|'                     # Ozon
    r'yandex\.market|'               # Яндекс.Маркет
    r'joom\.com'                    # Joom
    r')'
    r'[/\w\-\._~:/?#\[\]@!$&\'()*+,;=%]*$',  # Остальная часть URL
    re.IGNORECASE
)

def is_valid_url(url: str) -> bool:
    return bool(URL_REGEX.match(url))


# Начало добавления товара — выбираем маркетплейс
@add_product_router.message(Command(commands=["add"]))
async def cmd_add_start(message: types.Message, state: FSMContext):
    msg = await message.answer(
        "Выберите маркетплейс:",
        reply_markup=marketplace_keyboard()
    )
    
    await state.update_data(marketplace_msg_id=msg.message_id)
    await state.set_state(AddProductStates.marketplace)


# Обработка выбора маркетплейса или отмены
@add_product_router.callback_query(
    lambda c: c.data in [
        "marketplace_wildberries",
        "marketplace_ozon",
        "marketplace_yandex",
        "marketplace_joom",
        "cancel"
    ]
)
async def marketplace_chosen(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == "cancel":
        await state.clear()
        await callback.message.edit_text("Добавление товара отменено.")
        return

    marketplace = callback.data.split("_", 1)[1]
    await state.update_data(marketplace=marketplace)
    await callback.message.edit_text(
        "Введите ссылку на товар:\n"
        "Пример: https://www.wildberries.ru/catalog/246780526/detail.aspx"
    )
    await state.set_state(AddProductStates.product_url)


# Повторная отправка кнопок выбора маркетплейса, если пользователь что-то пишет не /add в состоянии marketplace
@add_product_router.message(
    StateFilter(AddProductStates.marketplace),
    ~Command(commands=["add"])
)
async def resend_marketplace_buttons(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if msg_id := data.get("marketplace_msg_id"):
        with suppress(TelegramBadRequest):
            await message.bot.delete_message(chat_id=message.from_user.id, message_id=msg_id)

    msg = await message.answer(
        "Пожалуйста, выберите маркетплейс:",
        reply_markup=marketplace_keyboard(),
    )
    await state.update_data(marketplace_msg_id=msg.message_id)


# Обработка ввода ссылки на товар
@add_product_router.message(AddProductStates.product_url)
async def product_url_entered(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not is_valid_url(url):
        await message.answer(
            "⚠️ Введена некорректная ссылка. Пожалуйста, введите корректную ссылку.\n"
            "Пример: https://www.wildberries.ru/catalog/246780526/detail.aspx"
        )
        return

    await state.update_data(product_url=url)
    await message.answer(
        "Введите целевую цену (в рублях):\n"
        "Пример: 5990"
    )
    await state.set_state(AddProductStates.target_price)


# Обработка ввода целевой цены и сохранение товара в БД
@add_product_router.message(AddProductStates.target_price)
async def target_price_entered(
    message: types.Message,
    state: FSMContext,
    conn: AsyncConnection,
    user_row: object | None = None
):
    price_text = message.text.strip()
    if not price_text.isdigit():
        await message.answer(
            "⚠️ Введено некорректное число. Пожалуйста, введите целевую цену целым числом (например, 5990)."
        )
        return

    target_price = int(price_text)
    if target_price <= 0:
        await message.answer(
            "⚠️ Цена должна быть больше нуля. Попробуйте снова."
        )
        return

    data = await state.get_data()
    marketplace = data.get("marketplace")
    product_url = data.get("product_url")

    if not marketplace or not product_url:
        await message.answer("Произошла ошибка. Повторите /add заново.")
        await state.clear()
        return

    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO products (user_id, marketplace, product_url, target_price)
            VALUES (%s, %s, %s, %s);
            """,
            (user_row.telegram_id, marketplace, product_url, target_price)
        )

    await message.answer(
        f"✅ Товар успешно добавлен:\n"
        f"Маркетплейс: {marketplace.title()}\n"
        f"Ссылка: {product_url}\n"
        f"Целевая цена: {target_price} ₽"
    )
    await state.clear()
