import pytest


@pytest.mark.asyncio
async def test_delete_me(client, create_user):
    # Create admin
    admin = await create_user(
        email='admin@foxminded.com',
        password='AdminPass123!',
        first_name='First_Admin',
        last_name='Last_Admin',
        roles=['admin'],
        is_superuser=False,
    )

    # Login as admin
    response = await client.post('/login', json={'email': admin.email, 'password': 'AdminPass123!'})
    assert response.status_code == 200
    token_admin = response.json()['access_token']

    # Try to delete own admin profile
    response = await client.delete('/me', headers={'Authorization': f'Bearer {token_admin}'})
    assert response.status_code == 403
    data = response.json()
    assert data['detail'] == 'Admin cannot delete own profile'
