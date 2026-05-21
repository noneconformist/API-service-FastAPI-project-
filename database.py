from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = 'postgresql+asyncpg://docker_user:docker_password@db:5432/docker_db'


engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)  # type: ignore

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
