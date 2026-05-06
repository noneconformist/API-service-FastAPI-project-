import pytest


@pytest.mark.asyncio
async def test_change_password(client, random_email):
    email = random_email
    payload = {'email': email, 'password': 'StrongPass123!'}

    # register
    response = await client.post('/register', json=payload)
    assert response.json()['msg'] == 'User registered successfully'

    # request reset password
    response = await client.post('/forgot-password', json={'email': email})
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data

    token = data['token']

    # reset password using token
    new_password = 'MerlinManson83$'
    response = await client.post('/reset-password', json={'token': token, 'password': new_password})
    assert response.status_code == 200
    assert response.json()['detail'] == 'Password successfully changed'

    # check login using new password
    login_response = await client.post('/login', json={'email': email, 'password': new_password})
    assert response.status_code == 200
    assert 'access_token' in login_response.cookies
