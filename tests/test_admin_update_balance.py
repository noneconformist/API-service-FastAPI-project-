import pytest


@pytest.mark.asyncio
async def test_admin_update_balance_remains_none(client, create_user):
    # Create admin
    admin = await create_user(
        email='admin_update@foxminded.com',
        password='AdminPass123!',
        first_name='Admin_firstname',
        last_name='Admin_lastname',
        roles=['admin'],
    )

    # Login as admin
    response = await client.post('/login', json={'email': admin.email, 'password': 'AdminPass123!'})
    assert response.status_code == 200
    token = response.json()['access_token']

    # Try to update the admin profile and set the balance
    response = await client.patch(
        '/me',
        headers={'Authorization': f'Bearer {token}'},
        json={'balance': 100},  # try to make active balance
    )
    assert response.status_code == 200
    data = response.json()

    # The balance should remain "none"
    assert data['balance'] is None
