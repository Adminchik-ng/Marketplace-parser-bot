import asyncio
import random
import re
import logging
from typing import Tuple, Optional
# from playwright.async_api import async_playwright, Page, BrowserContext
from undetected_playwright.async_api import async_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


async def check_product_existence_by_text(page: Page) -> bool:
    """
    Проверяет наличие товара по тексту страницы visible_text.
    Ищет тексты отсутствия товара и положительные индикаторы.
    Поиск текста — регистр-независимый.
    Возвращает False, если найден текст об отсутствии товара,
    True — если найден хотя бы один из положительных текстов,
    Иначе возвращает True (считаем, что товар есть).
    """
    
    visible_text = await page.evaluate("() => document.body.innerText")

    absence_patterns = [
        re.compile(r"этот товар закончился", re.IGNORECASE),
        re.compile(r"такой страницы не существует", re.IGNORECASE),
        re.compile(r"произошла ошибка!", re.IGNORECASE),
    ]
    positive_patterns = [
        re.compile(r"о товаре", re.IGNORECASE),
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


async def find_price_element(page: Page):
    price_element = await page.query_selector('[data-widget="webPrice"]')
    if price_element:
        return price_element
    elements = await page.query_selector_all("xpath=//*[contains(text(), '₽')]")
    for elem in elements:
        is_visible = await elem.is_visible()
        text = (await elem.inner_text()).strip()
        if is_visible and text:
            return elem
    price_element = await page.query_selector(".price")
    if price_element:
        return price_element
    return None


async def fetch_product_data(
    user_id: int,
    product_id: int,
    url: str,
    min_price: int,
    target_price: int,
    context: BrowserContext
) -> Tuple[int, int, Optional[int], Optional[str], Optional[int],  Optional[str], int, str]:
    """
    Возвращает кортеж:
    (user_id, product_id, price_or_none, product_name_or_none, min_price, last_error_or_none, target_price, url)
    """
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="load", timeout=30000)
        # await asyncio.sleep(random.uniform(2, 2.7))

        is_exists = await check_product_existence_by_text(page)
        if not is_exists:
            logger.info(f"Item {product_id} not found: {url}")
            await page.close()
            return (user_id, product_id, None, None, min_price, "Товар не найден", target_price, url)

        await page.wait_for_selector("h1", state='visible', timeout=30000)
        product_name = (await page.inner_text("h1")).strip()

        price_element = await find_price_element(page)
        if not price_element:
            logger.info(f"Price element not found: {url}")
            await page.close()
            return (user_id, product_id, None, product_name, min_price, "Товар не найден", target_price, url)

        price_text = (await price_element.inner_text()).strip()
        clean_price_text = re.sub(r'\s+', '', price_text)
        price_match = re.search(r'(\d+)', clean_price_text)
        price = int(price_match.group(1)) if price_match else None

        await page.close()
        if min_price and price:
            if int(price) <= int(min_price):
                logger.info(f"Price is less than min price: {url}")
                return (user_id, product_id, price, product_name, price, None, target_price, url)
            else:
                return (user_id, product_id, price, product_name, min_price, None, target_price, url)
        else:
            return (user_id, product_id, price, product_name, price, None, target_price, url)

    except Exception as e:
        logger.error(f"Error fetching product data in ozon: {url} - {e}")
        return (user_id, product_id, None, None, min_price, "Товар не найден", target_price, url)


async def fetch_product_data_with_semaphore(
        sem: asyncio.Semaphore,
        user_id: int,
        product_id: int,
        url: str,
        min_price: int,
        target_price: int,
        context: BrowserContext
    ):
    async with sem:
        return await fetch_product_data(user_id, product_id, url, min_price, target_price, context)


async def process_many_ozon_tasks(
    products_data: list[Tuple[int, int, str, int, int]],
    max_concurrent: int = 3
):
    async with async_playwright() as p:
        chromium_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-infobars"
        ]

        browser = await p.chromium.launch(
            headless=True,  
            args=chromium_args)
        
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

        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru'] });
            """
        )
        
        sem = asyncio.Semaphore(max_concurrent)

        tasks = []
        for user_id, product_id, url, min_price, target_price in products_data:
            tasks.append(
                fetch_product_data_with_semaphore(
                    sem, user_id, product_id, url, min_price, target_price, context
                )
            )

        results = await asyncio.gather(*tasks)

        await context.close()
        await browser.close()

        return results


if __name__ == "__main__":
    products_data = [
        (1, 101, "https://www.ozon.ru/product/sumka-kross-bodi-na-plecho-1962754411/", 500, 450),
        (1, 101, "https://www.ozon.ru/product/sumka-kross-bodi-na-plecho-1962754411/", 500, 450),
        (1, 101, "https://www.ozon.ru/product/sumka-kross-bodi-na-plecho-1962754411/", 500, 450),
        (1, 101, "https://www.ozon.ru/product/sumka-kross-bodi-na-plecho-1962754411/", 500, 450),
        (2, 102, "https://www.ozon.ru/product/your-product-url-2/", 300, 280),
        (3, 103, "https://ozon.ru/t/cBGw8Nk", 1000, 900),
    ]

    results = asyncio.run(process_many_ozon_tasks(products_data, max_concurrent=3))

    for res in results:
        user_id, product_id, price, product_name, min_price, _, target_price, url = res
        print(f"User: {user_id}, Product: {product_id}, URL: {url}")
        if product_name:
            print(f"Название товара: {product_name}")
        if price is not None:
            print(f"Цена: {price} ₽")
        else:
            print("Цена не найдена")
        print(f"Минимальная цена для оповещения: {min_price}, Целевая цена: {target_price}")
        print()
