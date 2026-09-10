from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
# expire_on_commit=False：提交后仍可读取 ORM 实例属性，避免响应序列化触发额外 IO
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
