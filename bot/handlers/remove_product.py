from math import prod
from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from psycopg import AsyncConnection
from contextlib import suppress
from database import db

from ..states.states import RemoveProductStates


remove_product_router = Router()


@remove_product_router.message(Command(commands=["remove"]))
async def cmd_remove_start(message: types.Message, state: FSMContext, conn: AsyncConnection):
    user_id = message.from_user.id

    products = await db.products.get_user_active_products(conn, user_id=user_id)

    if not products:
        await message.answer("У вас нет товаров для удаления.")
        return

    builder = InlineKeyboardBuilder()

    for product_id, product_name, product_url in products:
        text = f"{product_name}\n{product_url}" if product_name else product_url
        builder.button(text=text, callback_data=f"remove_{product_id}")

    builder.button(text="❌ Отмена", callback_data="remove_cancel")
    builder.adjust(1)  # Можно менять число для кнопок в ряду

    sent_message = await message.answer(
        "Выберите товар для удаления:", reply_markup=builder.as_markup()
    )

    await state.update_data(remove_msg_id=sent_message.message_id)
    await state.set_state(RemoveProductStates.choosing_product)


@remove_product_router.callback_query(
    StateFilter(RemoveProductStates.choosing_product),
    lambda c: c.data and (c.data.startswith("remove_") or c.data == "remove_cancel")
)
async def process_remove_callback(
    callback: types.CallbackQuery, state: FSMContext, conn: AsyncConnection
):
    data = callback.data
    user_id = callback.from_user.id


    if data == "remove_cancel":
        await callback.message.answer("Удаление отменено.")
        # Удаляем сообщение с кнопками полностью
        with suppress(TelegramBadRequest):
            await callback.message.delete()
        await state.clear()
        await callback.answer() 
        return

    try:
        product_id = int(data.split("_", 1)[1])
    except (ValueError, IndexError):
        await callback.message.answer("Некорректный выбор товара.")
        await callback.answer()
        return

    product = await db.products.get_product_by_id_and_user(conn, product_id=product_id, user_id=user_id)

    if not product:
        await callback.message.answer("Товар не найден или у вас нет прав для удаления.")
        await callback.answer()
        return

    product_name, product_url = product

    await db.products.delete_product_by_id(conn, product_id=product_id)

    # Удаляем сообщение с кнопками и отправляем новое с подтверждением
    with suppress(TelegramBadRequest):
        await callback.message.delete()

    await callback.message.answer(f'Товар "{product_name if product_name else product_url}" удален из отслеживания.')

    await callback.answer()  # Убираем «часики» у кнопки
    await state.clear()


@remove_product_router.message(
    StateFilter(RemoveProductStates.choosing_product),
    ~Command(commands=["remove"])
)
async def resend_remove_keyboard(message: types.Message, state: FSMContext, conn: AsyncConnection):
    data = await state.get_data()
    old_msg_id = data.get("remove_msg_id")

    # Удаляем предыдущее сообщение с кнопками, если есть
    with suppress(TelegramBadRequest):
        if old_msg_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)

    # Загружаем товары заново
    user_id = message.from_user.id
    
    products = await db.products.get_user_active_products(conn, user_id=user_id) 
    
    if not products:
        await message.answer("У вас нет товаров для удаления.")
        await state.clear()
        return

    builder = InlineKeyboardBuilder()
    for product_id, product_name, product_url in products:
        text = f"{product_name}\n{product_url}" if product_name else product_url
        builder.button(text=text, callback_data=f"remove_{product_id}")

    builder.button(text="❌ Отмена", callback_data="remove_cancel")
    builder.adjust(1)

    sent_message = await message.answer("Выберите товар для удаления:", reply_markup=builder.as_markup())
    await state.update_data(remove_msg_id=sent_message.message_id)
