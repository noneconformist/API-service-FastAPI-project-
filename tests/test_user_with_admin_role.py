import pytest
import pytest_asyncio
from sqlalchemy import select

from models import Role


@pytest_asyncio.fixture
async def admin_role(db_session):
    result = await db_session.execute(select(Role).where(Role.name == 'admin'))
    role = result.scalars().first()
    if not role:
        role = Role(name='admin')
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
    return role


@pytest.mark.asyncio
async def test_user_with_admin_role_is_retained(client, create_user, db_session, admin_role):
    user = await create_user(
        email='admin@foxminded.com', password='AdminPass123!', is_superuser=True
    )
    user.roles.append(admin_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert any(role.name == 'admin' for role in user.roles)
