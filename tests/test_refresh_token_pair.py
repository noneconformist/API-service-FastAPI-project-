import pytest


@pytest.mark.asyncio
async def test_refresh_tokens(client, create_user):
    #  Create user
    user = await create_user(
        email='anton@foxminded.com',
        password='UserPass123!',
        first_name='Anton',
        last_name='Galkin',
        is_superuser=False,
    )

    #  Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']

    # Renew token pair using the endpoint /refresh
    response = await client.post('/refresh', headers={'Authorization': f'Bearer {refresh_token}'})
    assert response.status_code == 200

    new_tokens = response.json()
    assert 'access_token' in new_tokens
    assert 'refresh_token' in new_tokens

    # Check that the new token pair is different from the old two.
    assert new_tokens['access_token'] != access_token
    assert new_tokens['refresh_token'] != refresh_token

    # The new access_token should work for protected endpoints.
    response = await client.get(
        '/me', headers={'Authorization': f'Bearer {new_tokens["access_token"]}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == 'anton@foxminded.com'
