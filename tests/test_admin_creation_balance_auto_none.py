import pytest


@pytest.mark.asyncio
async def test_admin_creation_balance_auto_none(client, create_user):
    # Create an admin with a balance of 100
    admin = await create_user(
        email='admin_autobalance@foxminded.com',
        password='AdminPass123!',
        first_name='Admin_firstname',
        last_name='Admin_lastname',
        roles=['admin'],
    )
    # Force the balance in the database (simulating an incorrect value)
    admin.balance = 100

    # Login as admin
    response = await client.post('/login', json={'email': admin.email, 'password': 'AdminPass123!'})
    assert response.status_code == 200
    token = response.json()['access_token']

    # Request a profile via /me
    response = await client.get(
        '/me',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    data = response.json()

    # The balance must be "none", even if there was a different value in the database.
    assert data['balance'] is None
