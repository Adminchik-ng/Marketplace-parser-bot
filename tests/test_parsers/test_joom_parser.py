# Исходная функция
import pytest
from tests.test_parsers.mocks import MockPage
from unittest.mock import AsyncMock
from bot.parsers.joom import check_product_exists, find_product_name 


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