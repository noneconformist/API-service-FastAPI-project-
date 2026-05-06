from datetime import datetime

import pytest
from sqlalchemy import select

from models import User


@pytest.mark.asyncio
async def test_login_updates_last_activity(client, create_user, db_session):
    # Create user
    user = await create_user(
        email='user@foxminded.com',
        password='UserPass123!',
        is_superuser=False,
    )

    old_last_activity = user.last_activity_at

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data

    # Check that last_activity_at have been updated
    result = await db_session.execute(select(User).where(User.id == user.id))
    refreshed = result.scalars().first()
    assert refreshed.last_activity_at is not None
    assert old_last_activity is None or refreshed.last_activity_at > old_last_activity


@pytest.mark.asyncio
async def test_get_me_updates_last_activity(client, create_user):
    # Create user
    user = await create_user(
        email='user@foxminded.com',
        password='UserPass123!',
        is_superuser=False,
        first_name='User_first_name',
        last_name='User_last_name',
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    token = response.json()['access_token']

    old_last_activity = user.last_activity_at

    # GET /me
    response = await client.get('/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    # Check that last_activity_at has changed
    new_last_activity = datetime.fromisoformat(response.json()['last_activity_at'])
    assert old_last_activity is None or new_last_activity > old_last_activity


@pytest.mark.asyncio
async def test_update_me_updates_last_activity(client, create_user):
    # Create user
    user = await create_user(
        email='user@foxminded.com',
        password='UserPass123!',
        is_superuser=False,
        first_name='OldFirst',
        last_name='OldLast',
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    token = response.json()['access_token']

    old_last_activity = user.last_activity_at

    # PATCH /me
    update_payload = {'first_name': 'NewFirst'}
    response = await client.patch(
        '/me', json=update_payload, headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['first_name'] == 'NewFirst'

    # Check that last_activity_at has changed
    new_last_activity = datetime.fromisoformat(data['last_activity_at'])
    assert old_last_activity is None or new_last_activity > old_last_activity
