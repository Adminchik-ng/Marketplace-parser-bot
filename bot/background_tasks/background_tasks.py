import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from database import db
import bot.db_pool_singleton.db_pool_singleton as global_pool
from bot.parsers.wildberries import process_many_wb_tasks

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def scheduled_task():
    pool = global_pool.db_pool_global

    if pool is None:
        logger.error("DB pool is not initialized!")
        raise RuntimeError("DB pool is not initialized!")

    # Получаем продукты из базы
    async with pool.acquire() as conn:
        products = await db.products.get_products_items_for_parsing(conn=conn)

    products_id_and_urls_and_min_prices = [
        (product_id, product_url, min_price)
        for product_id, product_url, marketplace, min_price in products
        if marketplace == "wildberries"
    ]

    if not products_id_and_urls_and_min_prices:
        return

    # Запускаем парсинг Wildberries
    products_after_parsing = await process_many_wb_tasks(products_id_and_urls_and_min_prices=products_id_and_urls_and_min_prices)

    if products_after_parsing:
        async with pool.acquire() as conn:
            for product_id, current_price, product_name, min_price, last_error in products_after_parsing:
                if last_error:
                    await db.products.change_product_price_and_error(
                        conn=conn,
                        product_id=product_id,
                        current_price=current_price,
                        product_name=product_name if product_name else None,
                        min_price=min_price,
                        last_error= last_error,
                        is_active=False
                    )
                else:
                    await db.products.change_product_price_and_error(
                        conn=conn,
                        product_id=product_id,
                        current_price=current_price,
                        product_name=product_name if product_name else None,
                        min_price=min_price,
                        last_error= last_error,
                        is_active=True
                    )

async def on_startup():
    """
    Запуск планировщика задач.
    """
    scheduler.add_job(scheduled_task, 'interval', seconds=20)
    scheduler.start()
