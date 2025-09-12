import re
import logging
from contextlib import suppress
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from asyncpg import Connection

from database import db  # Ваш модуль с функциями БД
from ..states.states import AddProductStates
from ..keyboards.keyboards import marketplace_keyboard

logger = logging.getLogger(__name__)
add_product_router = Router()


VALID_MARKETPLACES = {"wildberries", "ozon", "yandex", "joom"}

URL_REGEX = re.compile(
    r'^https?://(?:www\.)?'
    r'('
    r'wildberries\.ru|'           # Wildberries
    r'ozon\.ru|'                 # Ozon
    r'((?:[\w-]+\.)*yandex\.ru)|' # yandex.ru с любыми поддоменами
    r'yandex\.market|'           # Яндекс.Маркет
    r'joom\.(com|ru)'
    r')'
    r'[/\w\-\._~:/?#\[\]@!$&\'()*+,;=%]*$', # Остальная часть URL
    re.IGNORECASE
)



def is_valid_url(url: str) -> bool:
    return bool(URL_REGEX.match(url))


# Начало добавления товара — выбираем маркетплейс
@add_product_router.message(Command(commands=["add"]))
async def cmd_add_start(message: types.Message, state: FSMContext, *, conn: Connection):
    user_id = message.from_user.id
    
    result = await db.join_query.get_user_role_and_active_products_count(conn=conn, user_id=user_id)

    if result is None:
        await message.answer("⚠️ Упс! Не удалось получить данные пользователя. Попробуйте повторить чуть позже. 🙇‍♂️")
        await state.clear()
        return

    role, current_count = result
    is_admin = (role == "admin") 

    if not is_admin and current_count >= 5:
        await message.answer("⚠️ Максимум — 5 товаров на пользователя. К сожалению, сейчас нельзя добавить больше, но мы уже работаем над расширением! 🙏✨")
        await state.clear() 
        return
    
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
        with suppress(TelegramBadRequest):
            # Удаляем сообщение с кнопками выбора
            await callback.message.delete()
        await callback.message.answer("Добавление товара отменено.")
        return

    marketplace = callback.data.split("_", 1)[1]
    await state.update_data(marketplace=marketplace)
    await callback.message.edit_text(
        "Введите ссылку на товар или воспользуйтесь командой /cancel для отмены.",
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
    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("Добавление товара отменено.")
        return
    
    url = message.text.strip()
    if not is_valid_url(url):
        await message.answer(
            "⚠️ Введена некорректная ссылка. Пожалуйста, попробуйте ещё раз или введите /cancel, чтобы отменить добавление товара."
        )
        return

    await state.update_data(product_url=url)
    await message.answer(
        "Введите целевую цену (в рублях) или введите /cancel, чтобы отменить добавление товара."
    )
    await state.set_state(AddProductStates.target_price)


# Обработка ввода целевой цены и сохранение товара в БД
@add_product_router.message(AddProductStates.target_price)
async def target_price_entered(
    message: types.Message,
    state: FSMContext,
    conn: Connection,         # asyncpg.Connection (middleware должен передавать)
    user_row: Optional[object] = None,
):
    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("Добавление товара отменено.")
        return
    
    price_text = message.text.strip()

    if not price_text.isdigit():
        await message.answer(
            "⚠️ Введено некорректное число, введите целую цену (например, 5990) или /cancel для отмены."
        )
        return

    target_price = int(price_text)
    if target_price <= 0:
        await message.answer(
            "⚠️ Цена должна быть больше нуля, пожалуйста, попробуйте снова или введите /cancel для отмены."
        )
        return

    data = await state.get_data()
    marketplace = data.get("marketplace")
    product_url = data.get("product_url")

    if not marketplace or not product_url:
        await message.answer("Произошла ошибка. Повторите /add заново.")
        await state.clear()
        return

    if user_row is None:
        await message.answer("Ошибка авторизации пользователя. Попробуйте позже.")
        await state.clear()
        return

    # Безопасно получаем telegram_id из user_row (объекта или dict)
    user_id = getattr(user_row, "telegram_id", None) or user_row.get("telegram_id", None)
    if user_id is None:
        await message.answer("Не удалось получить ID пользователя. Попробуйте позже.")
        await state.clear()
        return

    try:
        await db.products.add_product(
            conn=conn,
            user_id=user_id,
            marketplace=marketplace,
            product_url=product_url,
            target_price=target_price
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}", exc_info=True)
        await message.answer("Произошла ошибка при добавлении товара. Попробуйте позже.")
        await state.clear()
        return

    await message.answer(
        f"✅ Товар успешно добавлен:\n"
        f"Маркетплейс: {marketplace.title()}\n"
        f"Ссылка: {product_url}\n"
        f"Целевая цена: {target_price} ₽"
    )
    await state.clear()
