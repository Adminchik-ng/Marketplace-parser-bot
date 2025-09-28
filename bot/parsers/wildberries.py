import asyncio
import re
import random
import time
import logging
from typing import Optional, Union, Tuple
from playwright.async_api import async_playwright, Page, Browser

    
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
async def check_product_exists(page: Page) -> bool:
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
        re.compile(r"по вашему запросу ничего не найдено", re.IGNORECASE),
        re.compile(r"нет\s*в\s*наличии", re.IGNORECASE)
    ]
    positive_patterns = [
        re.compile(r"артикул", re.IGNORECASE)
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


async def get_discount_price_wb(page: Page) -> Union[int, str]:
    """
    Получает цену со скидкой на уже загруженной странице.
    Если цены нет — возвращает строку "Цена не найдена".
    """
    
    price_locator = page.locator(
    "span[class*='priceBlockWalletPrice'], span[class*='redPrice']"
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

    discount_keywords = ["final", "discount", "sale", "red-price", "wallet-price"]
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
        product_name_el = await page.wait_for_selector("h1", timeout=10000)
        if product_name_el is None:
            return None
        product_name = (await product_name_el.inner_text()).strip()
        return product_name
    except Exception as e:
        logger.error(f"Error while getting product name: {e}", exc_info=True)
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
    products_id_and_urls_and_min_price: Tuple[int, int, str, int, int],
) -> Tuple[int, int, Optional[int], Optional[str], Optional[int], Optional[str], int, str]:
    """
    Одна задача: создаёт контекст и страницу, загружает URL,
    проверяет наличие товара и получает цену и название.
    """
    user_id = products_id_and_urls_and_min_price[0]
    product_id = products_id_and_urls_and_min_price[1]
    url = products_id_and_urls_and_min_price[2]
    min_price = products_id_and_urls_and_min_price[3]
    target_price = products_id_and_urls_and_min_price[4]

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
    await page.goto(url, wait_until="load", timeout=30000)    
    await asyncio.sleep(random.uniform(2.0, 2.7))
    
    await wait_for_full_load(page)

    # Проверяем наличие товара
    exists = await check_product_exists(page)
    if not exists:
        logger.warning("Item not found in marketplace")
        await context.close()
        return (user_id, product_id, None, None, min_price, "Товар не найден", target_price, url)

    # Получаем цену
    price = await get_discount_price_wb(page)

    # Получаем название
    name = await get_wb_product_name(page)

    await context.close()

    if isinstance(price, int) and name:
        logger.info(f"Price: {price} ₽, item: {name}")
        if min_price:
            if int(price) <= int(min_price):
                return (user_id, product_id, price, name, price, None, target_price, url)
            else:
                return (user_id, product_id, price, name, min_price, None, target_price, url)
        else:
            return (user_id, product_id, price, name, price, None, target_price, url)
        
    elif isinstance(price, int):
        logger.info(f"Founded only price: {price} ₽")
        if min_price:
            if int(price) <= int(min_price):
                return (user_id, product_id, price, None, price, None, target_price, url)
            else:
                return (user_id, product_id, price, None, min_price, None, target_price, url)
        else:
            return (user_id, product_id, price, None, price, None, target_price, url)

    else:
        logger.info("Price not found")
        return (user_id, product_id, None, None, min_price, "Товар не найден", target_price, url)


async def process_many_wb_tasks(
    products_id_and_urls_and_min_prices: list[Tuple[int, int, str, int, int]],
    max_concurrent: int = 5
) -> list[Tuple[int, int, Optional[int], Optional[str], Optional[int], Optional[str], int, str]]:
    """
    Запускает несколько одновременных задач по списку url и возвращает результаты.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # режим 'headless' можно менять
        semaphore = asyncio.Semaphore(max_concurrent)

        async def sem_task(product_info):
            async with semaphore:
                return await single_task(browser, product_info)

        tasks = [asyncio.create_task(sem_task(info)) for info in products_id_and_urls_and_min_prices]
        results = await asyncio.gather(*tasks)

        await browser.close()

        return results


if __name__ == "__main__":
    products_id_and_urls_and_min_prices = [
        # (user_id, product_id, url, min_price, target_price)
        # (1, 1, "https://www.wildberries.ru/caавыфаtalog/24678chhxhx0526/detail.aspx", 0, 0),
        # (1, 2, "https://www.wildberries.ru/catalog/246780526/detail.aspx", 0, 0),
        # (1, 3, "https://www.wildberries.ru/catalog/378236125/detail.aspx?targetUrl=SG", 0, 0),
        # (1, 4, "https://www.wildberries.ru/catalog/378236125/detail.aspx?targetUrl=SG", 0, 0),
        # (1, 4, "https://www.wildberries.ru/catalog/378236125/detail.aspx?targetUrl=SG", 0, 0),
        (1, 4, "https://www.wildberries.ru/catalog/447895670/detail.aspx?targetUrl=MI", 0, 0),
        (1, 4, "https://www.wildberries.ru/catalog/377844111/detail.aspx", 0, 0),
    ]

    start_time = time.time()
    results = asyncio.run(process_many_wb_tasks(products_id_and_urls_and_min_prices, max_concurrent=10))
    logger.info(f"Результаты: {results}")
    logger.info(f"Время выполнения: {time.time() - start_time:.2f} секунд")

