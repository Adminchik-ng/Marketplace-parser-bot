import asyncio
import re
import random
import logging
from typing import Optional, Tuple, List
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import re

async def check_product_exists(page: Page) -> bool:
    """
    Проверяет наличие товара по видимому тексту страницы.
    Ищет тексты отсутствия товара и положительные индикаторы.
    Поиск текста — регистр-независимый.
    Возвращает False, если найден текст об отсутствии товара,
    True — если найден хотя бы один из положительных текстов,
    Иначе возвращает True (считаем, что товар есть).
    """
    visible_text = await page.evaluate("() => document.body.innerText")

    absence_patterns = [
        re.compile(r"ой! что-то пошло не так", re.IGNORECASE),
        re.compile(r"упс\.", re.IGNORECASE),
        re.compile(r"страница, которую вы ищете, не существует\.", re.IGNORECASE),
        re.compile(r"товар раскупили", re.IGNORECASE)
    ]
    positive_patterns = [
        re.compile(r"описание", re.IGNORECASE)
    ]

    for pattern in absence_patterns:
        if pattern.search(visible_text):
            logger.info(f"Finded absence text: '{pattern.pattern}'")
            return False

    for pattern in positive_patterns:
        if pattern.search(visible_text):
            logger.info(f"Finded positive text: '{pattern.pattern}'")
            return True

    logger.info("Not finded absence or positive text, return True")
    return True



async def find_product_name(page: Page) -> Optional[str]:
    selectors = [
        'h1.root___e0mAF.collapsed___tnXms',
        'h1.product-title',
        'div.product-title',
        'h1',
        'h2',
        'h3'
    ]
    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=2000)
            if element:
                text = (await element.text_content()) or ""
                text = text.strip()
                if text and len(text) > 5:
                    return text
        except PlaywrightTimeoutError:
            continue

    headers = await page.query_selector_all('h1, h2, h3')
    longest_text = ""
    for header in headers:
        try:
            text = (await header.text_content()) or ""
            text = text.strip()
            if text and len(text) > len(longest_text):
                longest_text = text
        except Exception:
            continue
    if longest_text and len(longest_text) > 5:
        return longest_text

    elements = await page.query_selector_all("xpath=//*[string-length(normalize-space(text())) > 10]")
    for elem in elements:
        try:
            if await elem.is_visible():
                text = (await elem.text_content()) or ""
                text = text.strip()
                if text and not re.search(r'\d+[ ., ]*₽', text):
                    return text
        except Exception:
            continue

    return None


async def find_price(page: Page) -> Optional[str]:
    possible_tags = ['span', 'div', 'p', 'strong', 'b']
    currency_symbols = ['₽', '$', '€']


    for tag in possible_tags:
        elements = await page.query_selector_all(tag)
        for elem in elements:
            try:
                if await elem.is_visible():
                    text = (await elem.text_content()) or ""
                    text = text.strip()
                    if any(symbol in text for symbol in currency_symbols):
                        if re.search(r'\d[\d\s\u00a0.,]*', text):
                            return text
            except Exception:
                continue


    xpath_expr = "//*[contains(text(), '₽') or contains(text(), '$') or contains(text(), '€')]"
    elements = await page.query_selector_all(f"xpath={xpath_expr}")
    for elem in elements:
        try:
            if await elem.is_visible():
                text = (await elem.text_content()) or ""
                text = text.strip()
                if re.search(r'\d[\d\s\u00a0.,]*', text):
                    return text
        except Exception:
            continue


    return None



def parse_price(text: str) -> Optional[int]:
    text = text.strip()
    match = re.search(r'(\d[\d\s\u00a0.,]*\d|\d)\s*₽', text)
    if not match:
        return None
    price_str = match.group(1)
    price_str = price_str.replace(' ', '').replace('\u00a0', '').replace('.', '').replace(',', '')
    try:
        return int(price_str)
    except ValueError:
        logger.error(f"Invalid price string: '{price_str}' after parsing '{text}'")
        return None

async def wait_for_full_load(page, timeout=30000):
    await page.wait_for_load_state("load")  # дождаться полной загрузки страницы

    check_interval = 1000
    max_checks = timeout // check_interval
    last_html_size = 0
    stable_iterations = 0
    required_stable_iterations = 3

    for _ in range(max_checks):
        try:
            html = await page.content()
        except Exception:
            # Если не получилось получить контент (страница все еще обновляется), ждем и повторяем
            await page.wait_for_timeout(check_interval)
            continue

        current_size = len(html)
        if current_size == last_html_size:
            stable_iterations += 1
            if stable_iterations >= required_stable_iterations:
                break
        else:
            stable_iterations = 0

        last_html_size = current_size
        await page.wait_for_timeout(check_interval)


async def single_task(
    browser: Browser,
    product_info: Tuple[int, int, str, Optional[int], Optional[int]]
) -> Tuple[int, int, Optional[int], Optional[str], Optional[int], Optional[str], Optional[int], Optional[str]]:
    user_id, product_id, url, min_price, target_price = product_info


    context = await browser.new_context(
        user_agent=(
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1300, "height": 1000},
        java_script_enabled=True,
        locale="ru-RU",
        bypass_csp=True,
    )
    
    
    page = await context.new_page()


    try:
        await page.goto(url, wait_until="load", timeout=30000)    
        await asyncio.sleep(random.uniform(2.5, 5.5))  # задержка для эмуляции поведения пользователя

        await wait_for_full_load(page)

        exists = await check_product_exists(page)
        if not exists:
            logger.info(f"Item {product_id} not found: {url}")
            return (user_id, product_id, None, None, min_price, "Товар не найден", target_price, url)


        price_text = await find_price(page)
        price = parse_price(price_text) if price_text else None


        name = await find_product_name(page)


        if price is not None and name:
            logger.info(f"Price: {price} ₽, item: {name}")
            if min_price is not None:
                if int(price) <= int(min_price):
                    return (user_id, product_id, price, name, price, None, target_price, url)
                else:
                    return (user_id, product_id, price, name, min_price, None, target_price, url)
            else:
                return (user_id, product_id, price, name, price, None, target_price, url)
        elif price is not None:
            logger.info(f"Finded only price: {price} ₽")
            if min_price is not None:
                if int(price) <= int(min_price):
                    return (user_id, product_id, price, None, price, None, target_price, url)
                else:
                    return (user_id, product_id, price, None, min_price, None, target_price, url)
            else:
                return (user_id, product_id, price, None, price, None, target_price, url)
        else:
            logger.info("Price not found")
            return (user_id, product_id, None, None, min_price, "Цена не найдена", target_price, url)


    except Exception as e:
        logger.error(f"Error in single_task {product_id}: {e}")
        return (user_id, product_id, None, None, min_price, f"Ошибка обработки", target_price, url)
    finally:
        await context.close()


async def process_many_joom_tasks(
    products_info: List[Tuple[int, int, str, Optional[int], Optional[int]]],
    max_concurrent: int = 5
) -> List[Tuple[int, int, Optional[int], Optional[str], Optional[int], Optional[str], Optional[int], Optional[str]]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def sem_task(product_info):
            async with semaphore:
                return await single_task(browser, product_info)

        tasks = [asyncio.create_task(sem_task(info)) for info in products_info]
        results = await asyncio.gather(*tasks)

        await browser.close()

        return results


if __name__ == "__main__":
    products_to_check = [
        (1, 6545, "https://www.joom.ru/ru/products/6720faa03b1958015bbfba65?variant_id=6720faa03b1958b85bbfba74", 1000, 1200),
        # (1, 6545, "https://www.joom.ru/ru/products/6545eaeed9587a019dacd12e", 1000, 1200),
        # (1, 6545, "https://www.joom.ru/ru/products/6545eaeed9587a019dacd12e", 1000, 1200),
        # (2, 7890, "https://www.joom.ru/ru/products/another-product-url", 500, 700),
        (2, 7890, "https://www.joom.ru/ru/products/6539d273fff928018dbd4b43?variant_id=6539d273fff928588dbd4b46", 500, 700),
        # (2, 7890, "https://www.joom.ru/ru/products/67e6373a447cb5012e42ecf8?openPayload=%7B%22position%22%3A1%7D&variant_id=67e6373a447cb5262e42ecfa", 500, 700),
        # Добавьте свои товары тут
    ]

    results = asyncio.run(process_many_joom_tasks(products_to_check, max_concurrent=3))

    for result in results:
        user_id, product_id, price, name, min_price, status, target_price, url = result
        logger.info(
            f"User {user_id}, Product {product_id}, Price: {price}, Name: {name}, "
            f"Min: {min_price}, Status: {status}, Target: {target_price}, URL: {url}"
        )


