import pytest


@pytest.mark.asyncio
async def test_get_me(client, create_user):
    # Create user
    user = await create_user(
        email='anton@foxminded.com',
        password='UserPass123!',
        first_name='Anton',
        last_name='Galkin',
        is_superuser=False,
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    token = response.json()['access_token']

    # Get profile
    response = await client.get('/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    data = response.json()
    assert data['email'] == 'anton@foxminded.com'
    assert 'id' in data
    assert 'balance' in data
    assert 'block_status' in data
