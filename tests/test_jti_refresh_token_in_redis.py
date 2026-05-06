import jwt
import pytest


@pytest.mark.asyncio
async def test_login_refresh_token_exists_in_redis(
    client, create_user, redis_client_fixture, config_fixture
):
    """Check token exist in Redis after login log in"""

    user = await create_user(email='user@foxminded.com', password='UserPass123!')

    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    refresh_token = response.json()['refresh_token']

    # decode token to get jti
    decoded = jwt.decode(
        refresh_token,
        config_fixture.JWT_SECRET_KEY,
        algorithms=[config_fixture.JWT_ALGORITHM],
    )
    jti = decoded.get('jti')
    assert jti is not None

    # check redis key exists
    exist = redis_client_fixture.exists(f'refresh_token:{jti}')
    assert await exist == 1, "The token doesn't exist in Redis"

    # check redis value matches token
    value = await redis_client_fixture.get(f'refresh_token:{jti}')
    assert value == refresh_token, 'Stored refresh token value does not match refresh_token'
