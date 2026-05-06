import pytest


@pytest.mark.asyncio
async def test_regular_user_cannot_access_other_profile(client, create_user):
    # Create two users
    user1 = await create_user(
        email='user1@foxminded.com', password='UserPass123!', is_superuser=False
    )
    user2 = await create_user(
        email='user2@foxminded.com', password='UserPass124!', is_superuser=False
    )

    # Login as user1
    response = await client.post('/login', json={'email': user1.email, 'password': 'UserPass123!'})
    assert response.status_code == 200
    token = response.json()['access_token']

    # Trying to access user2's profile.
    update_payload = {'block_status': True}
    response = await client.patch(
        f'/users/{user2.id}/profile',
        json=update_payload,
        headers={'Authorization': f'Bearer {token}'},
    )

    # Check that access is denied
    assert response.status_code == 403
    data = response.json()
    assert 'Superuser privileges required' in data['detail']
