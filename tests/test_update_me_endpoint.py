import pytest


@pytest.mark.asyncio
async def test_update_me(client, create_user):
    # Create user
    user = await create_user(
        email='anton@foxminded.com', password='UserPass123!', is_superuser=False
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    token = response.json()['access_token']

    # Data for update
    update_payload = {
        'first_name': 'Updated name',
        'last_name': 'Updated last name',
    }

    # Patch profile
    response = await client.patch(
        '/me', json=update_payload, headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200

    data = response.json()
    assert data['first_name'] == 'Updated name'
    assert data['last_name'] == 'Updated last name'
