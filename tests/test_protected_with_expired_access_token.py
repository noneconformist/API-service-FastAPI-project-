import asyncio

import pytest


@pytest.mark.asyncio
async def test_protected_with_expired_token(client, create_user):
    # register
    user = await create_user(
        email='anton@foxminded.com',
        password='UserPass123!',
        first_name='Anton',
        last_name='Galkin',
        is_superuser=False,
    )

    # login
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    access_token = response.json()['access_token']

    # wait while access_token expire (60 seconds)
    await asyncio.sleep(70)

    # request to a secure endpoint with an expired token
    response = await client.get('/me', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Unauthorized'
