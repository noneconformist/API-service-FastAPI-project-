import pytest


@pytest.mark.asyncio
async def test_superuser_access(client, create_user):
    superuser = await create_user(is_superuser=True)

    response = await client.post(
        '/login',
        json={
            'email': superuser.email,
            'password': 'StrongPass123!',
        },
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    response = await client.get('/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_access(client, create_user):
    admin = await create_user(
        email='admin@example.com',
        password='StrongPass123!',
        roles=['admin'],
    )

    response = await client.post(
        '/login',
        json={
            'email': admin.email,
            'password': 'StrongPass123!',
        },
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    response = await client.get('/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_regular_user_denied(client, create_user):
    user = await create_user(is_superuser=False)

    response = await client.post(
        '/login',
        json={
            'email': user.email,
            'password': 'StrongPass123!',
        },
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    response = await client.get('/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
