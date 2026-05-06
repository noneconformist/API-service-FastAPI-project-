import pytest


@pytest.mark.asyncio
async def test_superuser_update_user_profile(client, create_user):
    # Create user
    user = await create_user(
        email='user@foxminded.com', password='UserPass123!', is_superuser=False
    )

    # Create superuser
    superuser = await create_user(
        email='admin@foxminded.com', password='AdminPass123!', is_superuser=True
    )

    # Login as superuser
    response = await client.post(
        '/login', json={'email': superuser.email, 'password': 'AdminPass123!'}
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    # Update user profile (make block_status = True)
    update_payload = {
        'first_name': 'BlockedUser',
        'block_status': True,
    }
    response = await client.patch(
        f'/users/{user.id}/profile',
        json=update_payload,
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200

    data = response.json()
    assert data['first_name'] == 'BlockedUser'
    assert data['block_status'] is True
