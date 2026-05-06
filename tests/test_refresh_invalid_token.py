import pytest


@pytest.mark.asyncio
async def test_refresh_invalid_token(client, create_user):
    #  Create user
    user = await create_user(
        email='anton@foxminded.com',
        password='UserPass123!',
        first_name='FirstNameUser',
        last_name='LastNameUser',
        is_superuser=False,
    )

    #  Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    assert response.status_code == 200

    # Try to refresh tokens with an obviously invalid refresh_token
    invalid_refresh_token = 'this_is_not_a_valid_token'
    refresh_token = invalid_refresh_token

    # Renew token pair using the endpoint /refresh
    response = await client.post('/refresh', headers={'Authorization': f'Bearer {refresh_token}'})
    assert response.status_code == 401

    data = response.json()
    assert data['detail'] == 'Unauthorized'
