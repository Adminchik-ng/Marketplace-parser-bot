import pytest
from tests.test_parsers.mocks import MockPage, MockPageWithLocator
from unittest.mock import AsyncMock
from bot.parsers.wildberries import check_product_exists, get_discount_price_wb, get_wb_product_name


@pytest.mark.parametrize("page_text, expected_result", [
    ("Артикул: 123", True),
    ("Упс. Произошла ошибка", True),
    ("Страница, которую вы ищете, не существует.", True),
    ("Товар раскупили", True),
    ("По вашему запросу ничего не найдено", False),
    ("Некоторый произвольный текст без маркеров", True),
    ("Нет в наличии", False),
    ("Товар раскупили. Страница, которую вы ищете, не существует.", True),
    ("Описание товара: смартфон Apple iPhone. Товар в наличии.", True),
    ("Какой-то случайный текст с описанием", True),
])
async def test_check_product_exists(page_text, expected_result):

    page = AsyncMock()
    page.evaluate.return_value = page_text
    
    res = await check_product_exists(page=page)
    
    assert res == expected_result


@pytest.mark.parametrize("elements_data, expected", [
    # 1. Одна скидочная цена (с ключевым словом в классе)
    (
        [
            {"text": "1 000 ₽", "class": "price red-price", "tag": "span"},
            {"text": "1 200 ₽", "class": "price normal", "tag": "div"},
        ],
        1000,
    ),
    # 2. Несколько скидочных — выбирается минимальная
    (
        [
            {"text": "900 ₽", "class": "discount final", "tag": "ins"},
            {"text": "800 ₽", "class": "wallet-price", "tag": "span"},
            {"text": "1 000 ₽", "class": "price normal", "tag": "span"},
        ],
        800,
    ),
    # 3. Нет скидочных, выбирается минимальная цена из всех
    (
        [
            {"text": "1 500 ₽", "class": "price normal", "tag": "div"},
            {"text": "2 000 ₽", "class": "price normal", "tag": "span"},
        ],
        1500,
    ),
    # 4. Нет цен (текст не содержит валидных цен)
    (
        [
            {"text": "Нет цены", "class": "", "tag": "div"},
            {"text": "Обсуждается", "class": "price", "tag": "span"},
        ],
        "Цена не найдена",
    ),
    # 5. Некорректные и пустые строки
    (
        [
            {"text": "", "class": "red-price", "tag": "span"},
            {"text": "abc ₽", "class": "discount", "tag": "div"},
        ],
        "Цена не найдена",
    ),
    # 6. Цены с разными форматами пробелов и nbsp
    (
        [
            {"text": "1\u00a0000 ₽", "class": "red-price final", "tag": "span"},
            {"text": "1 200 ₽", "class": "price", "tag": "div"},
        ],
        1000,
    ),
    # 7. Отсутствие классов и тегов, но текст с ценой
    (
        [
            {"text": "1 300 ₽", "class": "", "tag": ""},
            {"text": "1 100 ₽", "class": None, "tag": None},
        ],
        1100,
    ),
    # 8. Цена равна 0 ₽
    (
        [
            {"text": "0 ₽", "class": "discount", "tag": "ins"},
            {"text": "100 ₽", "class": "price", "tag": "div"},
        ],
        100,
    ),
])
async def test_get_discount_price_wb(elements_data, expected):
    page = MockPageWithLocator(elements_data)
    result = await get_discount_price_wb(page)
    assert result == expected
    

@pytest.mark.parametrize("selectors_data, expected", [
    ({"h1": "Название товара"}, "Название товара"),
    ({"h1": "  Название с пробелами  "}, "Название с пробелами"),
    ({}, None),  # Эмулируем таймаут (отсутствие h1)
])
async def test_get_wb_product_name(selectors_data, expected):
    page = MockPage(selectors_data)
    result = await get_wb_product_name(page)
    assert result == expected