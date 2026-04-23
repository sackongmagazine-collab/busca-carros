from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Render fornece postgresql:// mas SQLAlchemy async exige postgresql+asyncpg://
_db_url = settings.database_url
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_db_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        import app.models.user  # noqa: F401
        import app.models.search  # noqa: F401
        import app.models.alert  # noqa: F401
        import app.models.subscription  # noqa: F401
        import app.models.dealer  # noqa: F401
        import app.models.fraud_report  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
