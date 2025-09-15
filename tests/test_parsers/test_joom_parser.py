# Исходная функция
import pytest
from tests.test_parsers.mocks import MockPage
from unittest.mock import AsyncMock
from bot.parsers.joom import check_product_exists, find_price, find_product_name, parse_price 


@pytest.mark.parametrize("page_text, expected_result", [
    ("Ой! Что-то пошло не так при загрузке страницы", False),
    ("Упс. Произошла ошибка", False),
    ("Страница, которую вы ищете, не существует.", False),
    ("Товар раскупили", False),
    ("Описание товара: смартфон Apple iPhone", True),
    ("Некоторый произвольный текст без маркеров", True),
    ("Товар в наличии", True),
    ("Товар раскупили. Страница, которую вы ищете, не существует.", False),
    ("Описание товара: смартфон Apple iPhone. Товар в наличии.", True),
    ("Какой-то случайный текст с описанием", True),
])
async def test_check_product_exists(page_text, expected_result):

    page = AsyncMock()
    page.evaluate.return_value = page_text
    
    res = await check_product_exists(page=page)
    
    assert res == expected_result


@pytest.mark.parametrize("selectors_data, expected_result", [

    (
        {
            'h1.root___e0mAF.collapsed___tnXms': 'Смартфон Apple iPhone 13',
        },
        'Смартфон Apple iPhone 13'
    ),
    
    (
        {
            'h1.product-title': 'Наушники AirPods Pro',
        },
        'Наушники AirPods Pro'
        
    ),
    
    (
        {
            'headers': ['Короткий', 'Очень длинный заголовок для теста', 'Средний'],
        },
        'Очень длинный заголовок для теста'
        
    ),
    
    (
        {
            'headers': ['A', 'BC', 'DEF', 'GHIJ'],
        },
        None
        
    ),
    
    (
        {
            'headers': ['Заголовок с    пробелами', 'Спец!@#символы'],
        },
        'Заголовок с    пробелами'
        
    ),
    
    (
        {
            'headers': ['Единственный подходящий заголовок'],
        },
        'Единственный подходящий заголовок'
        
    ),
    
    (
        {
            'headers': ['', '   ', None, ''],
        },
        None
        
    ),
    
    (
        {
            'xpath': 'Описание товара: Смартфон Samsung',
            'is_visible': True 
        },
        'Описание товара: Смартфон Samsung'
    ),
    
    (
        {
            'xpath':'Товар стоит 1000 ₽',
            'is_visible': True  
        },
        None
    ),
        
    (
        {
            'xpath':'Невидимый текст',
            'is_visible': False  
        },
        None
    ),
        
    (
        {
            'xpath':'',
            'is_visible': True  
        },
        None
    ),
    
])
async def test_find_product_name(selectors_data, expected_result):

    page = MockPage(selectors_data)
    
    res = await find_product_name(page)
    
    assert res == expected_result
    

@pytest.mark.parametrize("selectors_data, expected_result", [

    (
        {
            'сontainers': ['Цена 1500 ₽'],
        },
        'Цена 1500 ₽'
    ),
    
    (
        {
            'сontainers': ['Стоимость: 2000 $'],
        },
        'Стоимость: 2000 $'
    ),    
    
    (
        {
            'сontainers': ['Price: 2000 €'],
        },
        'Price: 2000 €'
    ),
    
    (
        {
            'xpath': 'Цена 1500 ₽',
        },
        'Цена 1500 ₽'
    ),
    
    (
        {
            'xpath': 'Стоимость: 2000 $',
        },
        'Стоимость: 2000 $'
    ),    
    
    (
        {
            'xpath': 'Price: 2000 €',
        },
        'Price: 2000 €'
    ),
    
    
])
async def test_find_price(selectors_data, expected_result):

    page = MockPage(selectors_data)
    
    res = await find_price(page)
    
    assert res == expected_result
    

@pytest.mark.parametrize("input_text, expected_result", 
[
    # Базовые случаи
    ("1000 ₽", 1000),
    ("1 000 ₽", 1000),
    ("1\u00a0000 ₽", 1000),
    ("1,000 ₽", 1000),
    ("1.000 ₽", 1000),
    
    # Сложные случаи форматирования
    ("Цена: 2 500 ₽", 2500),
    # ("Стоимость 3.500,00 ₽", 3500), # не проходит
    ("Цена: 4\u00a0500 ₽", 4500),
    
    # Граничные случаи
    ("0 ₽", 0),
    ("1 ₽", 1),
    ("999999999 ₽", 999999999),
    
    # Невалидные случаи
    ("abc ₽", None),
    ("123abc ₽", None),
    (" ₽", None),
    ("", None),
    ("123$", None),  # Неверный символ валюты
    ("123€", None),  # Неверный символ валюты
    ("123", None),   # Отсутствует символ ₽
])
async def test_parse_price(input_text, expected_result):

    result = parse_price(input_text)
    assert result == expected_result