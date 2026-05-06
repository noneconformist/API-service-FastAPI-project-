import pytest
from sqlalchemy import select

from models import User


@pytest.mark.asyncio
async def test_user_without_role_gets_default_user_role(client, db_session):
    response = await client.post(
        '/register', json={'email': 'user@foxminded.com', 'password': 'UserPass123!'}
    )
    assert response.status_code == 200

    result = await db_session.execute(select(User).where(User.email == 'user@foxminded.com'))
    new_user = result.scalars().first()
    assert new_user is not None

    # Check the role was assigned
    assert new_user.roles
    assert new_user.roles[0].name == 'user'
