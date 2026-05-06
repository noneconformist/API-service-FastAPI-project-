import pytest


@pytest.mark.asyncio
async def test_login(client, random_email):
    email = random_email
    # register
    payload = {'email': email, 'password': 'StrongPass123!'}
    response = await client.post('/register', json=payload)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['msg'] == 'User registered successfully'

    # login
    login_data = {'email': email, 'password': 'StrongPass123!'}
    response = await client.post('/login', json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert 'access_token' in response.cookies


@pytest.mark.asyncio
async def test_register_after_deletion(client, create_user):
    # Create user
    user = await create_user(
        email='anton@foxminded.com', password='UserPass123!', is_superuser=False
    )

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})

    assert response.status_code == 200
    token = response.json()['access_token']

    # delete profile
    response = await client.delete('/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json()['detail'] == 'Your profile deleted successfully'

    # login again should fail with 403
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    assert response.status_code == 404
    assert response.json()['detail'] == 'This account does not exist'

    # register again with same email → new account
    response = await client.post(
        '/register', json={'email': user.email, 'password': 'UserPass123!'}
    )
    assert response.status_code == 200
    assert response.json()['msg'] == 'User registered successfully'

    # login with new account should succeed
    response = await client.post('/login', json={'email': user.email, 'password': 'UserPass123!'})
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert 'access_token' in response.cookies
