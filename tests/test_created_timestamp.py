from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_created_at_set_on_registration(client, create_user):
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

    # GET /me
    response = await client.get('/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = response.json()

    # Check that created_at have been installed
    created_at = datetime.fromisoformat(data['created_at'])
    assert created_at is not None


@pytest.mark.asyncio
async def test_created_at_does_not_change_on_update(client, create_user):
    # # Create user
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

    old_created_at = user.created_at

    # PATCH /me
    update_payload = {'first_name': 'NewFirst'}
    response = await client.patch(
        '/me', json=update_payload, headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()

    # Check that created_at didn't update
    new_created_at = datetime.fromisoformat(data['created_at'])
    assert new_created_at == old_created_at
