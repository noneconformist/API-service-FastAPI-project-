from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_user_updates_names_updates_timestamp(client, create_user):
    # Create user with names
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

    old_updated_at = user.updated_at

    # Update names using patch /me
    update_payload = {'first_name': 'NewFirst', 'last_name': 'NewLast'}
    response = await client.patch(
        '/me', json=update_payload, headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()

    # Check that fields have been updated
    assert data['first_name'] == 'NewFirst'
    assert data['last_name'] == 'NewLast'

    # Check that updated_at has changed
    new_updated_at = datetime.fromisoformat(data['updated_at'])
    assert old_updated_at is None or new_updated_at > old_updated_at


@pytest.mark.asyncio
async def test_superuser_updates_block_status_updates_timestamp(client, create_user):
    # Create regular user
    user = await create_user(
        email='user@foxminded.com',
        password='UserPass123!',
        is_superuser=False,
        first_name='Anton',
        last_name='Galkin',
    )
    # Create superuser
    superuser = await create_user(
        email='admin@foxminded.com', password='AdminPass123!', is_superuser=True
    )

    # Login as superuser
    response = await client.post(
        '/login', json={'email': superuser.email, 'password': 'AdminPass123!'}
    )
    token = response.json()['access_token']

    old_updated_at = user.updated_at

    # Update block status
    update_payload = {'block_status': True}
    response = await client.patch(
        f'/users/{user.id}/profile',
        json=update_payload,
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    data = response.json()

    # Check that the field have been updated
    assert data['block_status'] is True

    # Check that updated_at has changed
    new_updated_at = datetime.fromisoformat(data['updated_at'])
    assert old_updated_at is None or new_updated_at > old_updated_at
