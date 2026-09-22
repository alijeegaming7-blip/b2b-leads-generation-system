from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import get_settings

settings = get_settings()

# SQLite needs aiosqlite driver + check_same_thread=False
_url = settings.DATABASE_URL
_is_sqlite = _url.startswith("sqlite")

_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# Proper connection pooling configuration
if _is_sqlite:
    # SQLite doesn't support connection pooling in async mode well
    _pool_kwargs = {"poolclass": NullPool}
else:
    # PostgreSQL/MySQL with proper pooling
    _pool_kwargs = {
        "poolclass": QueuePool,
        "pool_size": 5,           # Minimum connections
        "max_overflow": 10,       # Additional connections when needed
        "pool_timeout": 30,       # Seconds to wait for connection
        "pool_recycle": 3600,     # Recycle connections after 1 hour
        "pool_pre_ping": True,    # Verify connections before use
    }

engine = create_async_engine(
    _url,
    echo=settings.ENV == "development",
    connect_args=_connect_args,
    **_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes providing database session with proper cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables - used for SQLite dev mode instead of Alembic."""
    from app.models import Base  # noqa: F401 - registers all models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
