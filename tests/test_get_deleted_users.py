import pytest


@pytest.mark.asyncio
async def test_delete_me(client, create_user):
    # Create user
    user = await create_user(
        email='user@foxminded.com', password='UserPass123!', is_superuser=False
    )

    # Create admin
    admin = await create_user(
        email='admin@foxminded.com',
        password='AdminPass123!',
        first_name='First_Admin',
        last_name='Last_Admin',
        roles=['admin'],
        is_superuser=False,
    )

    # Create superuser
    superuser = await create_user(
        email='superuser@foxminded.com', password='SuperuserPass123!', is_superuser=True
    )

    # Login as superuser
    response = await client.post(
        '/login', json={'email': superuser.email, 'password': 'SuperuserPass123!'}
    )
    assert response.status_code == 200
    superuser_token = response.json()['access_token']

    # Superuser delete user
    response = await client.delete(
        f'/users/{user.id}/profile',
        headers={'Authorization': f'Bearer {superuser_token}'},
    )
    assert response.status_code == 200

    data = response.json()
    assert data['detail'] == f'User with id={user.id} deleted successfully'

    # Login as admin
    response = await client.post('/login', json={'email': admin.email, 'password': 'AdminPass123!'})
    assert response.status_code == 200
    admin_token = response.json()['access_token']

    # Admin gets deleted users
    response = await client.get(
        '/users?deleted_only=true', headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 200
    deleted_users = response.json()

    # Проверяем, что наш удалённый user там есть
    assert any(u['id'] == user.id for u in deleted_users)

    # Дополнительно проверяем ключевые поля
    deleted_user = next(u for u in deleted_users if u['id'] == user.id)
    assert deleted_user['is_active'] is False
    assert deleted_user['email'] == user.email
