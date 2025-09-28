import asyncio
import random
import re
import logging
from typing import Tuple, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright.async_api import TimeoutError



# Настройка логгера
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
        re.compile(r"Тут ничего нет", re.IGNORECASE),
        re.compile(r"Попробуйте вернуться назад или поищите что-нибудь другое.", re.IGNORECASE),
        re.compile(r"Нет в продаже", re.IGNORECASE),
        re.compile(r"Такого товара у нас нет", re.IGNORECASE),
    ]
    positive_patterns = [
        re.compile(r"Артикул Маркета", re.IGNORECASE),
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
    """
    Устойчивый поиск элемента с ценой на Яндекс.Маркете.
    Использует несколько вариантов селекторов, включая частичные совпадения атрибутов,
    а также поиск по контексту и видимым элементам с символом ₽.
    """
    # Попытки по разным селекторам — более универсальные и частичные совпадения по атрибутам
    selectors = [
        '[data-widget*="Price"]',          # Частичное совпадение data-widget
        '[data-autotest-id*="price"]',     # Частичное совпадение data-autotest-id
        '[data-zone-name*="price"]',       # Частичное совпадение data-zone-name
        '[class*="price"]',                 # Классы, содержащие слово price
        'span',                           # Последний запасной вариант — все span
        'div',                            # Добавлен див на случай смены тега
    ]

    for sel in selectors:
        elems = await page.query_selector_all(sel)
        for elem in elems:
            if await elem.is_visible():
                text = (await elem.inner_text()).strip()
                if not text:
                    continue
                # Ищем цену с символом ₽ и цифрами
                if '₽' in text and re.search(r'\d', text):
                    digits = ''.join(filter(str.isdigit, text))
                    # Цена должна содержать не менее двух цифр
                    if len(digits) >= 2:
                        return elem

    # Если не нашли по селекторам, ищем по тексту всего документа
    elements = await page.query_selector_all("xpath=//*[contains(text(), '₽')]")
    for elem in elements:
        if await elem.is_visible():
            text = (await elem.inner_text()).strip()
            if text:
                digits = ''.join(filter(str.isdigit, text))
                if len(digits) >= 2:
                    return elem

    return None


def parse_price(text: str) -> Optional[int]:
    """
    Извлекает число из строки с ценой.
    Убирает пробелы и спецсимволы, оставляет только цифры.
    Берёт первое числовое значение.
    """
    clean_text = re.sub(r'[^\d\s]', '', text)
    price_match = re.search(r'\d[\d\s]*\d|\d', clean_text)
    if price_match:
        price_str = price_match.group(0).replace(' ', '').replace('\u2006', '')  # очищаем пробелы
        try:
            return int(price_str)
        except ValueError:
            return None
    return None



async def find_product_name(page: Page) -> Optional[str]:
    """
    Поиск названия товара с использованием нескольких стратегий.
    """
    selectors = [
        'h1[data-auto*="productCardTitle"]',
        'h1[data-additional-zone*="title"]',
        'h1',
        'div[data-zone-name*="title"]',
    ]
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=4000)
            elem = await page.query_selector(sel)
            if elem:
                text = (await elem.inner_text()).strip()
                if text and len(text) > 5:
                    return text
        except TimeoutError:
            continue

    headers = await page.query_selector_all('h1, h2, h3')
    for h in headers:
        text = (await h.inner_text()).strip()
        if text and len(text) > 5:
            return text

    return None


async def fetch_product_data(
    user_id: int,
    product_id: int,
    url: str,
    min_price: int,
    target_price: int,
    context: BrowserContext
) -> Tuple[int, int, Optional[int], Optional[str], int, Optional[str], int, str]:
    """
    Возвращает кортеж:
    (user_id, product_id, price_or_none, product_name_or_none, min_price, last_error_or_none, target_price, url)
    """
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="load", timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))

        is_exists = await check_product_existence_by_text(page)
        if not is_exists:
            logger.info(f"Item {product_id} not found: {url}")
            await page.close()
            return (user_id, product_id, None, None, min_price, "Товар не найден", target_price, url)

        product_name = await find_product_name(page)
        if not product_name:
            logger.info(f"Product name not found: {url}")
            await page.close()
            return (user_id, product_id, None, None, min_price, "Название не найдено", target_price, url)

        price_element = await find_price_element(page)
        if not price_element:
            logger.info(f"Price element not found: {url}")
            await page.close()
            return (user_id, product_id, None, product_name, min_price, "Цена не найдена", target_price, url)

        price_text = (await price_element.inner_text()).strip()
        clean_price_text = re.sub(r'\s+', '', price_text)
        price_match = re.search(r'(\d+)', clean_price_text)
        price = int(price_match.group(1)) if price_match else None

        await page.close()

        if price is None:
            logger.info(f"Cannot parse price: {url}")
            return (user_id, product_id, None, product_name, min_price, "Цена не распознана", target_price, url)

        if min_price:
            if int(price) <= int(min_price):
                logger.info(f"Price is less than min price: {url} Price: {price}, Min price: {min_price}")
                return (user_id, product_id, price, product_name, price, None, target_price, url)
            else:
                return (user_id, product_id, price, product_name, min_price, None, target_price, url)
        else:
            return (user_id, product_id, price, product_name, price, None, target_price, url)

    except Exception as e:
        logger.error(f"Error while fetching product data in Yandex Market: {url} - {e}")
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


async def process_many_yandex_market_tasks(
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

        browser = await p.chromium.launch(headless=True, args=chromium_args)
        context = await browser.new_context(
            user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       f"(KHTML, like Gecko) Chrome/{random.randint(100, 115)}.0.0.0 Safari/537.36",
            viewport={"width": random.randint(1000, 1400), "height": random.randint(800, 1200)},
            locale="ru-RU",
            java_script_enabled=True,
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

        tasks = [
            fetch_product_data_with_semaphore(
                sem, user_id, product_id, url, min_price, target_price, context
            )
            for user_id, product_id, url, min_price, target_price in products_data
        ]

        results = await asyncio.gather(*tasks)

        await context.close()
        await browser.close()

        return results


if __name__ == "__main__":
    products_data = [
    #     (1, 501, "https://market.yandex.ru/card/besprovodnaya-zaryadka-magnet-wireless-power-bank-a27-1-20w-10000-mach-na-apple-iphone--vneshniy-akkumulyator-magsafe--poverbank-dlya-telefona--belyy/102496890633?do-waremd5=3DX-Vylp1N01nLo5Hm6Ojg&cpc=nRQuk_UGdVh_s6ci19KHi_PFuVn__PHq_WXsmGCh1flVPmvQyWX6R7xgjFiPzAEcW-lN8pJr_4rBuIwzOU9K2iWYKuujW9pVsCTbk_5GGoDdQYcPConeE0RMPY5BYKDIfZW0g-R6xNifLQiFTKiqRzEo4vTjlCRFtGvfYJhIYSu2mjIT_zLprWbYp0cWPnQf8ptlk28uaVx6X2AN-ZbkuncWKmzz7XhpKezLafqtHuammpws9VBtmPSo5c-wHTxP&ogV=-2", 1500, 1300),
    #     (2, 502, "https://market.yandex.ru/product--drugoi-tovar/0000000000", 2000, 1800),
    #     (3, 503, "https://market.yandex.ru/product--esche-odin-tovar/1234567890", 1000, 900),
        (3, 503, "https://market.yandex.ru/card/apple-besprovodnyye-naushniki-apple-airpods-4-s-shumopodavleniyem/103760694880?do-waremd5=-l5ou3SoJixabKtI6XVC1w&cpc=TwxnC3avKh_M_tdSv3Qc98GF6nY9nJ_BYtQrTdaac5k_pcJec2-YfIzizcRATNqrzZUdDUdxaQFSLHW11C8PvQMIGZ5WJJCpO7FApT4DUUL58J0cIfHC_EXx8hO8C6ieTtmoIHBandwxr3dPq7-747_rIOCr-Xtf8hfgpRWEM7OpjpaSRH4HHtrVL-WtdZXYSxL_V3pKsPyxe4x5FTUTWTZSNvqvmZXpw3oZ9f_r4x0w22QR6v73fMcjUUW7V13CRYDDrjl2mARWkU6itsaozF4XaNs_yrWjktD4DQW03Krpd7q7L61n3ohYDeGnLAM2amdOrHD4faQdBWO1GUb-1bL-AN1Ok_YfXAoRdohiNk24Flvrx_LyXw%2C%2C&ogV=-4", 1000, 900),
        (3, 503, "https://market.yandex.ru/card/korpus-zalman-minitower-p10-mini-tower-plastikstalderevosteklo-5-slotov-rasshireniya/4511565227?do-waremd5=V2Ujf-g1Nqe4XPUi0HYDDQ&sponsored=1&cpc=TwxnC3avKh_qXNOvdM5o_oJXTLigqN6lWjoBAkrcWkysA9Bgaq3KZW6rP2oJcRGjw6Fo--iuT3MpMeCLSIsutNcQ13GcReVxe-y8COwhgG9-lB3CWsLZ_bGlNElJLnQrl_EJvjRuaPU-O7vqiHEZd7vGbEWDXTCVwtG6Nz84Gxhnao_egpD1zt3GTFSVi5cn3J28qnk7DwohQWxsvb5JiBInmjmTQjB30BgcNJa_9rMIIRfj8AQKFv1cxZR_UnICSIADfCk4GNhAVCJYMBfnnTz7LBBRPqegr_C3IZc9Z5UOFLmB7eLD-Z4KloDY4bt56VslozAj6Vx1etMWM2wbXBQI3iXGN4bG5sq3Imt7obktA4jZ5VegyQ%2C%2C&ogV=-4", 1000, 900),
    ]

    results = asyncio.run(process_many_yandex_market_tasks(products_data, max_concurrent=3))

    for res in results:
        user_id, product_id, price, product_name, min_price, last_error, target_price, url = res
        logger.info(f"User: {user_id}, Product: {product_id}, URL: {url}")
        if product_name:
            logger.info(f"Название товара: {product_name}")
        if price is not None:
            logger.info(f"Цена: {price} ₽")
        else:
            logger.info("Цена не найдена")
        logger.info(f"Минимальная цена для оповещения: {min_price}, Целевая цена: {target_price}")
        if last_error:
            logger.info(f"Ошибка/статус: {last_error}")
        logger.info("")
