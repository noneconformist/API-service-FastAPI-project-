import os
import uuid
from typing import Optional

import asyncpg
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from database import Base, get_db
from main import app, config, redis_client

load_dotenv()

USER = os.getenv('TEST_USER')
PASS = os.getenv('TEST_PASS')
HOST = os.getenv('TEST_HOST')
PORT = os.getenv('TEST_PORT')
BASE_DB = os.getenv('TEST_BASE_DB')
DB_NAME = os.getenv('TEST_DB_NAME')

TEST_DATABASE_URL = f'postgresql+asyncpg://{USER}:{PASS}@{HOST}:{PORT}/{DB_NAME}'


@pytest_asyncio.fixture(scope='session', autouse=True, loop_scope='session')
async def setup_test_db():
    conn = await asyncpg.connect(
        user=USER, password=PASS, host=HOST, port=PORT, database=BASE_DB, timeout=15
    )

    try:
        await conn.execute(f'DROP DATABASE IF EXISTS {DB_NAME}')
        await conn.execute(f'CREATE DATABASE {DB_NAME}')
    finally:
        await conn.close()

    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await test_engine.dispose()
    conn = await asyncpg.connect(user=USER, password=PASS, host=HOST, port=PORT, database=BASE_DB)
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope='session')
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def db_session(db_engine):
    connection = await db_engine.connect()
    # start of transaction
    transaction = await connection.begin()
    # created a session bound to the connection
    session = AsyncSession(bind=connection, expire_on_commit=False)

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    await session.close()
    # rolled everything back
    await transaction.rollback()
    await connection.close()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope='function', loop_scope='session')
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url='http://testserver',
        follow_redirects=True,
    ) as ac:
        yield ac
        await ac.aclose()


@pytest.fixture
def random_email():
    return f'{uuid.uuid4().hex}@example.com'


@pytest_asyncio.fixture
async def create_user(db_session, random_email):
    async def _create_user(
        email: str | None = None,
        password: str = 'StrongPass123!',
        first_name: str | None = None,
        last_name: str | None = None,
        is_superuser: bool = False,
        roles: Optional[list[str]] = None,
    ):
        from core import pwd_context
        from models import User

        if email is None:
            email = random_email

        user = User(
            email=email,
            password=pwd_context.hash(password),
            is_superuser=is_superuser,
            first_name=first_name,
            last_name=last_name,
        )

        # roles for users (admin, user etc.)
        if roles:
            from models import Role

            for role_name in roles:
                role = await db_session.execute(select(Role).where(Role.name == role_name))
                role_obj = role.scalars().first()
                if not role_obj:
                    role_obj = Role(name=role_name)
                    db_session.add(role_obj)
                    await db_session.commit()
                    await db_session.refresh(role_obj)
                user.roles.append(role_obj)

        # Admin's balance = 0
        if any(role.name == 'admin' for role in user.roles):
            user.balance = 0

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


# Off check CSRF
load_dotenv('.env.test')


@pytest.fixture(scope='session', autouse=True)
def setup_test_env():
    os.environ['JWT_COOKIE_CSRF_PROTECT'] = 'False'


@pytest.fixture
def redis_client_fixture():
    return redis_client


@pytest.fixture
def config_fixture():
    return config
