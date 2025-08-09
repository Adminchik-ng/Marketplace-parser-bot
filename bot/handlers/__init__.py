from bot.handlers.add_product import add_product_router
from bot.handlers.admin import admin_router 
from bot.handlers.remove_product import remove_product_router
from bot.handlers.list_product import list_router
from bot.handlers.user import user_router
from bot.handlers.summary_product import summary_router
from bot.handlers.others import others_router

__all__ = ["add_product_router", "admin_router", "remove_product_router", "list_router", "user_router", "summary_router", "others_router"]