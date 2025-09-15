from typing import Optional
import pytest
import re
from bot.parsers.ozon import find_price_element
from tests.test_parsers.mocks import MockPage
from unittest.mock import AsyncMock
from bot.parsers.yandex_market import check_product_existence_by_text, find_price_element, parse_price, find_product_name


@pytest.mark.parametrize("page_text, expected_result", [
    ("Тут ничего нет", False),
    ("Попробуйте вернуться назад или поищите что-нибудь другое.", False),
    ("Нет в продаже", False),
    ("Товар и его название", True),
    ("Описание товара: смартфон Apple iPhone", True),
    ("Некоторый произвольный текст без маркеров", True),
    ("Товар в наличии", True),
    ("Такого товара у нас нет", False),
    ("Описание товара: смартфон Apple iPhone. Товар в наличии.", True),
    ("Артикул Маркета", True),
])
async def test_check_product_existence_by_text(page_text, expected_result):

    page = AsyncMock()
    page.evaluate.return_value = page_text
    
    res = await check_product_existence_by_text(page=page)
    
    assert res == expected_result
    

@pytest.mark.parametrize("selectors_data, expected_text_contains, expected_none", [
    # 1. Цена есть в первом селекторе
    (
        {'[data-widget*="Price"]': 'Цена 123 ₽', 'xpath': 'Цена 999 ₽', 'is_visible': True}, 
        '₽', 
        False
    ),
    # 2. Цена отсутствует в селекторах, есть в xpath
    (
        {'[data-widget*="Price"]': '', '[data-autotest-id*="price"]': '', 'xpath': 'Цена 999 ₽', 'is_visible': True}, 
        '₽', 
        False
    ),
    # 3. Нет цены вообще
    (
        {'[data-widget*="Price"]': '', '[data-autotest-id*="price"]': '', 'xpath': '', 'is_visible': True}, 
        None, 
        True
    ),
    # 4. Цена есть, но элемент невидимый, должен найти xpath
    (
        {'[data-widget*="Price"]': '1234 ₽', 'is_visible': False, 'xpath': '567 ₽', 'is_visible': True}, 
        '₽', 
        False
    ),
])
async def test_find_price_element_param(selectors_data, expected_text_contains, expected_none):
    page = MockPage(selectors_data)
    element = await find_price_element(page)
    if expected_none:
        assert element is None
    else:
        assert element is not None
        text = await element.inner_text()
        assert expected_text_contains in text
        assert re.search(r'\d', text)
        
        
@pytest.mark.parametrize("input_text, expected_price", [
    ("Цена 123 ₽", 123),                        # Простой кейс с ₽ и цифрами
    ("1 234 ₽", 1234),                         # Цена с пробелом (разделителем тысяч)
    ("₽ 5678", 5678),                          # ₽ в начале
    ("Цена: 99\u2006123₽", 99123),             # Цена с неразрывным пробелом \u2006
    ("abc123def", 123),                        # Число в середине текста без ₽
    ("Цена нет", None),                        # Нет числа
    ("₽", None),                              # Только символ ₽, без цифр
    ("", None),                               # Пустая строка
    ("Цена 12 34 56", 123456),                # Множество пробелов внутри числа
    ("Цена 12.345₽", 12345),                   # Точка в числе (будет отброшена)
])
def test_parse_price(input_text: str, expected_price: Optional[int]):
    result = parse_price(input_text)
    assert result == expected_price
    
    
@pytest.mark.parametrize(
    "selectors_data, expected_name",
    [
        (
            {'h1[data-auto*="productCardTitle"]': 'Product Title 12345'},
            'Product Title 12345'
        ),
        (
            {'h1[data-additional-zone*="title"]': 'Another Product Name'},
            'Another Product Name'
        ),
        (
            {'h1': 'Simple Product Name'},
            'Simple Product Name'
        ),
        (
            {'div[data-zone-name*="title"]': 'Div Title Product'},
            'Div Title Product'
        ),
        (
            {'headers': ['short', 'Header That Works']},
            'Header That Works'
        ),
        (
            {'headers': ['tiny', 'small']},
            None
        ),
        (
            {},  # Пустые данные
            None
        )
    ]
)
async def test_find_product_name_parametrized(selectors_data, expected_name):
    page = MockPage(selectors_data)
    result = await find_product_name(page)
    assert result == expected_name