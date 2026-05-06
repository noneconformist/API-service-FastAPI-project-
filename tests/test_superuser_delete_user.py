import pytest


@pytest.mark.asyncio
async def test_superuser_delete_user(client, create_user):
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

    # Delete user
    response = await client.delete(
        f'/users/{user.id}/profile',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200

    data = response.json()
    assert data['detail'] == f'User with id={user.id} deleted successfully'
