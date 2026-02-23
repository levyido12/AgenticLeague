import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# asyncpg requires ssl context object, not query params
connect_args = {}
if "neon.tech" in settings.database_url or "amazonaws" in settings.database_url:
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    settings.database_url, echo=False, connect_args=connect_args
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
