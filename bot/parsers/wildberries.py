import asyncio
from itertools import product
from math import prod
import re
import random
import time
import logging
from tkinter import N
from typing import Optional, Union, Tuple
from playwright.async_api import async_playwright, Page, Browser, TimeoutError
    
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_product_exists(page: Page) -> bool:
    """
    Асинхронно ждёт появления либо сообщения об отсутствии товара,
    либо появления любого из положительных индикаторов из списка positive_texts.
    Поиск текста — регистр-независимый.
    Возвращает False, если найден текст об отсутствии товара,
    True — если найден хотя бы один из положительных текстов.
    Таймаут ожидания — 5 секунд.
    Кроме того, выводит в лог текст, по которому найдено совпадение.
    """
    timeout_ms = 30000

    # Задача и текст для отсутствия товара
    absence_text = "по вашему запросу ничего не найдено"
    absence_task = asyncio.create_task(
        page.wait_for_selector(f"text=/{absence_text}/i", timeout=timeout_ms)
    )

    positive_texts = [
        "Артикул"
    ]

    # Создаем словарь: задача -> искомый текст
    positive_tasks_map = {
        asyncio.create_task(page.wait_for_selector(f"text=/{text}/i", timeout=timeout_ms)): text
        for text in positive_texts
    }

    pending = {absence_task, *positive_tasks_map.keys()}

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            try:
                await task
            except TimeoutError:
                # Не найден этот текст - просто пропускаем
                continue
            except Exception as e:
                logger.error(f"Ошибка при ожидании текста: {e}", exc_info=True)
                continue

            if task is absence_task:
                logger.info(f"Найден текст об отсутствии товара: '{absence_text}'")
                for t in pending:
                    t.cancel()
                return False

            if task in positive_tasks_map:
                found_text = positive_tasks_map[task]
                logger.info(f"Найден текст, подтверждающий существование товара: '{found_text}'")
                for t in pending:
                    t.cancel()
                return True

    logger.info("Не найдено подтверждающих текстов (таймаут). Считаем, что товар есть.")
    return True




async def get_discount_price_wb(page: Page) -> Union[int, str]:
    """
    Получает цену со скидкой на уже загруженной странице.
    Если цены нет — возвращает строку "Цена не найдена".
    """
    # Скроллим вниз для подгрузки динамического контента
    await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
    await asyncio.sleep(random.uniform(1.0, 2.0))

    price_locator = page.locator(
        "span[class*='price'], div[class*='price'], ins[class*='price']"
    )
    count = await price_locator.count()

    valid_prices = []
    for i in range(count):
        elem = price_locator.nth(i)
        text = (await elem.inner_text()).strip()
        match = re.search(r'(\d[\d\s]*\d)\s*₽', text)
        if not match:
            continue
        price_str = match.group(1).replace('\xa0', '').replace(' ', '')
        try:
            price_val = int(price_str)
        except ValueError:
            continue
        cls = (await elem.get_attribute('class')) or ""
        cls = cls.lower()
        tag = await elem.evaluate("(el) => el.tagName.toLowerCase()")
        valid_prices.append({"price": price_val, "class": cls, "tag": tag})

    if not valid_prices:
        return "Цена не найдена"

    discount_keywords = ["final", "discount", "sale"]
    discount_prices = [
        item["price"] for item in valid_prices if any(k in item["class"] for k in discount_keywords)
    ]

    if discount_prices:
        discount_price = min(discount_prices)
    else:
        discount_price = min(item["price"] for item in valid_prices)

    return discount_price


async def get_wb_product_name(page: Page) -> Optional[str]:
    """
    Получает название товара на уже загруженной странице.
    Возвращает None если название не найдено.
    """
    try:
        product_name_el = await page.wait_for_selector("h1", timeout=1500)
        product_name = (await product_name_el.inner_text()).strip()
        return product_name
    except Exception as e:
        logger.error(f"Ошибка при получении названия товара: {e}", exc_info=True)
        return None


async def single_task(
    browser: Browser,
    products_id_and_urls_and_min_price: Tuple[int, str, int],
) -> Tuple[int, Optional[int], Optional[str], Optional[int], str]:
    """
    Одна задача: создаёт контекст и страницу, загружает URL,
    проверяет наличие товара и получает цену и название.
    """
    
    product_id = products_id_and_urls_and_min_price[0]
    url = products_id_and_urls_and_min_price[1]
    min_price = products_id_and_urls_and_min_price[2]

    context = await browser.new_context(
        user_agent=(
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{random.randint(100, 115)}.0.0.0 Safari/537.36"
        ),
        viewport={"width": random.randint(1000, 1400), "height": random.randint(800, 1200)},
        java_script_enabled=True,
        locale="ru-RU",
        bypass_csp=True,
    )
    page = await context.new_page()

    # Переход на страницу
    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(2.5, 5.5))

    # Проверяем наличие товара
    exists = await check_product_exists(page)
    if not exists:
        logger.info("Товар не найден на маркетплейсе")
        await context.close()
        return (product_id, None, None, min_price, "Товар не найден")

    # Получаем цену
    price = await get_discount_price_wb(page)

    # Получаем название
    name = await get_wb_product_name(page)

    await context.close()

    if isinstance(price, int) and name:
        logger.info(f"Цена со скидкой: {price} ₽ на товар {name}")
        if min_price:
            if price <= min_price:
                return (product_id, price, name, price, None)
            else:
                return (product_id, price, name, min_price, None)
        else:
            return (product_id, price, name, price, None)
        
    elif isinstance(price, str):
        logger.info(f"Найдена только цена со скидкой: {price} ₽")
        if min_price:
            if price <= min_price:
                return (product_id, price, None, price, None)
            else:
                return (product_id, price, None, min_price, None)
        else:
            return (product_id, price, None, price, None)

    else:
        logger.info("Цена не найдена")
        return (product_id, None, None, min_price, "Товар не найден")


async def process_many_wb_tasks(products_id_and_urls_and_min_prices: list[(int, str, int)], max_concurrent: int = 5) -> list[(int, int, str, int)]:
    """
    Запускает несколько одновременных задач по списку url и возвращает результаты.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # здесь меняем режим открытия браузера
        semaphore = asyncio.Semaphore(max_concurrent)

        async def sem_task(url: str):
            async with semaphore:
                return await single_task(browser, url)  # возвращаем результат single_task

        tasks = [asyncio.create_task(sem_task(products_id_and_urls_and_min_price)) for products_id_and_urls_and_min_price in products_id_and_urls_and_min_prices]
        results = await asyncio.gather(*tasks)

        await browser.close()

        return results  # возвращаем список результатов


if __name__ == "__main__":
    urls = [
        "https://www.wildberries.ru/catalog/96313894/detail.aspx?targetUrl=MI",
        "https://www.wildberries.ru/catalog/185390527/detail.aspx",
        "https://www.wildberries.ru/catalog/378236125/detail.aspx?targetUrl=SG",
        "https://www.wildberries.ru/catalog/378236125/detail.aspx?targetUrl=SG",
    ]

    start_time = time.time()
    asyncio.run(process_many_wb_tasks(urls, max_concurrent=10))
    logger.info(f"Время выполнения: {time.time() - start_time:.2f} секунд")

