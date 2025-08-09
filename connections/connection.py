import logging
import asyncpg
from urllib.parse import quote

logger = logging.getLogger(__name__)


def build_pg_dsn(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
) -> str:
    """
    Формируем DSN строку для asyncpg.
    Логируется информация без пароля.
    """
    dsn = f"postgresql://{quote(user)}:{quote(password)}@{host}:{port}/{db_name}"
    logger.debug(
        f"Building PostgreSQL DSN (password omitted): "
        f"postgresql://{quote(user)}@{host}:{port}/{db_name}"
    )
    return dsn


async def log_db_version(connection: asyncpg.Connection) -> None:
    """
    Логирование версии сервера PostgreSQL.
    """
    try:
        version = await connection.fetchval("SELECT version();")
        logger.info(f"Connected to PostgreSQL version: {version}")
    except Exception as e:
        logger.warning(f"Failed to fetch DB version: {e}")


async def get_pg_connection(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
) -> asyncpg.Connection:
    """
    Получение одиночного подключения к PostgreSQL.
    """
    dsn = build_pg_dsn(db_name, host, port, user, password)
    try:
        connection = await asyncpg.connect(dsn)
        await log_db_version(connection)
        return connection
    except Exception:
        logger.exception("Failed to connect to PostgreSQL")
        raise


async def get_pg_pool(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    min_size: int = 1,
    max_size: int = 3,
    timeout: float | None = 10.0,
) -> asyncpg.Pool:
    """
    Создание пула подключений к PostgreSQL.
    """
    dsn = build_pg_dsn(db_name, host, port, user, password)
    try:
        pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            timeout=timeout,
        )
        async with pool.acquire() as connection:
            await log_db_version(connection)

        return pool
    except Exception:
        logger.exception("Failed to initialize PostgreSQL pool")
        raise
