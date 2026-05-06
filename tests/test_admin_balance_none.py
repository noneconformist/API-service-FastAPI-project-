import pytest


@pytest.mark.asyncio
async def test_admin_balance_none(client, create_user):
    # Create admin
    admin = await create_user(
        email='admin@foxminded.com',
        password='AdminPass123!',
        first_name='Admin_firstname',
        last_name='Admin_lastname',
        roles=['admin'],
    )

    # Login as admin
    response = await client.post('/login', json={'email': admin.email, 'password': 'AdminPass123!'})
    assert response.status_code == 200
    token = response.json()['access_token']

    # Check balance
    balance_response = await client.get('/me/balance', headers={'Authorization': f'Bearer {token}'})
    assert balance_response.status_code == 200
    data = balance_response.json()
    assert data['balance'] is None  # admin always none

    # Try to write off funds
    charge_response = await client.put('/me/balance', headers={'Authorization': f'Bearer {token}'})
    assert charge_response.status_code == 200
    charge_data = charge_response.json()
    assert charge_data['balance'] is None
    assert 'Admins cannot have an active balance' in charge_data['message']
