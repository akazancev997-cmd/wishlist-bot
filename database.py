import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base

_engine = None
_session_factory = None


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/wishlist.db")


def _ensure_engine():
    global _engine, _session_factory
    if _engine is None:
        db_url = get_db_url()
        _engine = create_async_engine(db_url, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine, _session_factory


def get_session() -> AsyncSession:
    _, factory = _ensure_engine()
    return factory()


async def init_db():
    engine, _ = _ensure_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
