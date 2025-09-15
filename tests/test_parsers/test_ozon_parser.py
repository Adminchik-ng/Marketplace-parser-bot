import pytest
from tests.test_parsers.mocks import MockElement, MockPageOzon
from unittest.mock import AsyncMock
from bot.parsers.ozon import check_product_existence_by_text, find_price_element


@pytest.mark.parametrize("page_text, expected_result", [
    ("Этот товар закончился", False),
    ("О товаре", True),
    ("Такой страницы не существует", False),
    ("Описание товара: смартфон Apple iPhone", True),
    ("Некоторый произвольный текст без маркеров", True),
    ("Товар в наличии", True),
    ("Произошла ошибка!", False),
    ("Описание товара: смартфон Apple iPhone. Товар в наличии.", True),
    ("Какой-то случайный текст с описанием", True),
])
async def test_check_product_existence_by_text(page_text, expected_result):

    page = AsyncMock()
    page.evaluate.return_value = page_text
    
    res = await check_product_existence_by_text(page=page)
    
    assert res == expected_result
    


@pytest.mark.parametrize(
    "selectors_data, expected_result",
    [
        # Тест 1: Цена есть в data-widget="webPrice"
        (
            {
                '[data-widget="webPrice"]': '1234 ₽',
            },
            '1234 ₽'
        ),

        # Тест 2: Цена только в XPath
        (
            {
                'xpath': ['Цена: 567 ₽'],
                'is_visible': [True]
            },
            'Цена: 567 ₽'
        ),

        # Тест 3: Цена в .price селекторе
        (
            {
                '.price': '999 ₽',
            },
            '999 ₽'
        ),

        # Тест 4: Нет цены вообще
        (
            {
                'xpath': [''],
                'is_visible': [True]
            },
            None
        ),

        # Тест 5: Первый data-widget
        (
            {
                '[data-widget="webPrice"]': '1234 ₽',
                'xpath': '567 ₽',
                'is_visible': [True]
            },
            '1234 ₽'
        ),

        # Тест 6: Несколько XPath элементов, первый видимый
        (
            {
                'xpath': ['100 ₽', '200 ₽', '300 ₽'],
                'is_visible': [True, False, True]
            },
            '100 ₽'
        ),

        # Тест 7: Все XPath элементы невидимые
        (
            {
                'xpath': ['100 ₽', '200 ₽'],
                'is_visible': [False, False]
            },
            None
        ),

        # Тест 8: Пустой текст в видимом элементе
        (
            {
                'xpath': [' '],
                'is_visible': [True]
            },
            None
        ),

        # Тест 9: Цена с пробелами
        (
            {
                'xpath': ['   456 ₽   '],
                'is_visible': [True]
            },
            '   456 ₽   '
        ),

        # Тест 10: Цена с дополнительным текстом
        (
            {
                'xpath': ['Стоимость: 789 ₽'],
                'is_visible': [True]
            },
            'Стоимость: 789 ₽'
        )
    ]
)
async def test_find_price_element(selectors_data, expected_result):
    page = MockPageOzon(selectors_data)
    result = await find_price_element(page)
    if isinstance(result, MockElement):
        result = await result.inner_text()
        assert result == expected_result
    else:    
        assert result == expected_result
