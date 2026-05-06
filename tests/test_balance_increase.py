import pytest


@pytest.mark.asyncio
async def test_balance_increases_on_login(client, create_user):
    # Create user
    user = await create_user(
        email='user@foxminded.com',
        password='UserPass123!',
        first_name='User_firstname',
        last_name='User_lastname',
        is_superuser=False,
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    token = response.json()['access_token']

    # Get balance
    balance_response = await client.get('/me/balance', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = balance_response.json()

    # The balance must increase by 15
    assert data['balance'] == 15
