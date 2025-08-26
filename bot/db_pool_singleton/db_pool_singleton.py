from typing import Optional
import asyncpg
from aiogram import Bot

bot_instance: Optional[Bot] = None

db_pool_global: Optional[asyncpg.Pool] = None
