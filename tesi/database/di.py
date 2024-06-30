from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from tesi.config import settings


def get_db_url() -> str:
    db_driver = ""

    match settings.db_type:
        case "sqlite":
            db_driver = "aiosqlite"
        case "postgresql":
            db_driver = "asyncpg"
        case "mysql" | "mariadb":
            db_driver = "aiomysql"

    db_full_url = ""

    if settings.db_type == "sqlite":
        db_full_url = f"{settings.db_type}+{db_driver}:///{settings.db_name}"
    else:
        db_full_url = f"{settings.db_type}+{db_driver}://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

    return db_full_url


engine = create_async_engine(url=get_db_url())


def get_session_maker() -> async_sessionmaker:
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
