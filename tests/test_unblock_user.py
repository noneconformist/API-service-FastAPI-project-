import pytest


@pytest.mark.asyncio
async def test_block_user(client, create_user):
    # Create user
    user = await create_user(
        email='user@foxminded.com',
        password='BlockPass123!',
        first_name='First_User',
        last_name='Last_User',
        is_superuser=False,
    )

    # Create admin
    admin = await create_user(
        email='admin@foxminded.com',
        password='AdminPass123!',
        first_name='First_Admin',
        last_name='Last_Admin',
        roles=['admin'],
        is_superuser=False,
    )

    # Login as admin
    response = await client.post('/login', json={'email': admin.email, 'password': 'AdminPass123!'})
    assert response.status_code == 200
    token_admin = response.json()['access_token']

    # Block user (admin's endpoint)
    block_response = await client.patch(
        f'/users/{user.id}/block?block=true', headers={'Authorization': f'Bearer {token_admin}'}
    )
    assert block_response.status_code == 200
    assert (
        f'User with id={user.id} has been blocked successfully' in block_response.json()['detail']
    )

    # Try login as user after block → denied
    blocked_login = await client.post(
        '/login', json={'email': user.email, 'password': 'BlockPass123!'}
    )
    assert blocked_login.status_code == 403
    error = blocked_login.json()
    assert 'This account has been blocked' in error['detail']

    # Unblock user (admin's endpoint)
    block_response = await client.patch(
        f'/users/{user.id}/block?block=false', headers={'Authorization': f'Bearer {token_admin}'}
    )
    assert block_response.status_code == 200
    assert (
        f'User with id={user.id} has been unblocked successfully' in block_response.json()['detail']
    )

    # Login as user after unblock → successfully
    response = await client.post('/login', json={'email': user.email, 'password': 'BlockPass123!'})
    assert response.status_code == 200
    tokens = response.json()
    assert 'access_token' in tokens
