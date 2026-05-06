import pytest
from sqlalchemy.future import select

from models import User


@pytest.mark.asyncio
async def test_delete_me(client, create_user, db_session):
    # Create user
    user = await create_user(
        email='anton@foxminded.com', password='UserPass123!', is_superuser=False
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    token = response.json()['access_token']

    # Delete profile
    response = await client.delete('/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    data = response.json()
    assert data['detail'] == 'Your profile deleted successfully'

    # Check that the is_deleted flag is set in the database.
    result = await db_session.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    assert db_user.is_active is False

    # A repeated login should return 404
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    assert response.status_code == 404
    assert response.json()['detail'] == 'This account does not exist'
