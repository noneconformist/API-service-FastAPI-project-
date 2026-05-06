import jwt
import pytest


@pytest.mark.asyncio
async def test_logout_blacklist(client, create_user, redis_client_fixture, config_fixture):
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

    # logout
    logout_response = await client.post(
        '/logout', headers={'Authorization': f'Bearer {access_token}'}
    )
    assert logout_response.status_code == 200
    assert logout_response.json()['msg'] == 'Logged out successfully'

    # decode token to get jti
    decoded = jwt.decode(
        access_token,
        config_fixture.JWT_SECRET_KEY,
        algorithms=[config_fixture.JWT_ALGORITHM],
    )
    print(decoded)
    jti = decoded.get('jti')
    assert jti is not None

    # check redis blacklist
    value = await redis_client_fixture.get(f'blacklist:{jti}')
    assert value == 'revoked'
