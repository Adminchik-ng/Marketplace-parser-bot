import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from database import db
import bot.db_pool_singleton.db_pool_singleton as global_pool
from bot.parsers.wildberries import process_many_wb_tasks
from bot.parsers.ozon import process_many_ozon_tasks
from bot.parsers.joom import process_many_joom_tasks
from bot.parsers.yandex_market import process_many_yandex_market_tasks
from bot.bot_send.bot_send import send_message

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def handle_parsing_results(pool, bot, parsed_products):
    if not parsed_products:
        return

    async with pool.acquire() as conn:
        for user_id, product_id, current_price, product_name, min_price, last_error, target_price, url in parsed_products:
            if last_error:
                await db.products.change_product_details_after_parsing(
                    conn=conn,
                    product_id=product_id,
                    current_price=current_price,
                    product_name=product_name if product_name else None,
                    min_price=min_price,
                    last_error=last_error,
                    is_active=False
                )
            else:
                if current_price <= target_price:
                    logger.info("Found minimal price for product_id=%d", product_id)
                    chat_id = await db.users.get_user_chat_id(conn=conn, user_id=user_id)
                    if chat_id:
                        await send_message(bot, chat_id=chat_id, current_price=current_price,
                                           product_name=product_name, target_price=target_price, url=url)
                    else:
                        logger.warning(f"For user_id={user_id} chat_id not found, message will not be sent.")

                await db.products.change_product_details_after_parsing(
                    conn=conn,
                    product_id=product_id,
                    current_price=current_price,
                    product_name=product_name if product_name else None,
                    min_price=min_price,
                    last_error=last_error,
                    is_active=True
                )


async def scheduled_task():
    logger.info("Scheduled task started")
    pool = global_pool.db_pool_global
    bot = global_pool.bot_instance

    if pool is None:
        logger.error("DB pool is not initialized!")
        raise RuntimeError("DB pool is not initialized!")

    async with pool.acquire() as conn:
        products = await db.products.get_products_items_for_parsing(conn=conn)

    tasks_map = {
        "wildberries": process_many_wb_tasks,
        "ozon": process_many_ozon_tasks,
        "joom": process_many_joom_tasks,
        "yandex": process_many_yandex_market_tasks,
    }

    # Группируем задачи по маркетплейсам
    tasks_by_marketplace = {key: [] for key in tasks_map.keys()}
    for user_id, product_id, product_url, marketplace, min_price, target_price in products:
        if marketplace in tasks_by_marketplace:
            tasks_by_marketplace[marketplace].append((user_id, product_id, product_url, min_price, target_price))

    # Обрабатываем парсинг и обновление базы для каждого маркетплейса
    for marketplace, process_func in tasks_map.items():
        tasks = tasks_by_marketplace[marketplace]
        if not tasks:
            continue
        
        parsed_products = await process_func(tasks)
        await handle_parsing_results(pool, bot, parsed_products)


async def on_startup():
    """
    Запуск планировщика задач.
    """
    scheduler.add_job(scheduled_task, 'interval', minutes=2)
    scheduler.start()
