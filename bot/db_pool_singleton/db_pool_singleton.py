from typing import Optional
import asyncpg

db_pool_global: Optional[asyncpg.Pool] = None
