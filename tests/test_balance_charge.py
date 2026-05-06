import pytest


@pytest.mark.asyncio
async def test_balance_to_charge(client, create_user):
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

    # Charge balance
    first_balance_response = await client.put(
        '/me/balance', headers={'Authorization': f'Bearer {token}'}
    )
    assert first_balance_response.status_code == 200
    data = first_balance_response.json()

    # The balance have to be 5
    assert data['balance'] == 5

    # Charge balance again
    second_balance_response = await client.put(
        '/me/balance', headers={'Authorization': f'Bearer {token}'}
    )
    assert second_balance_response.status_code == 400
    error = second_balance_response.json()

    # Get error message
    assert 'Insufficient funds' in error['detail']
