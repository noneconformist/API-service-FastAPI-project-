import pytest


@pytest.mark.asyncio
async def test_logout(client, random_email):
    email = random_email
    payload = {'email': email, 'password': 'StrongPass123!'}

    # register
    response = await client.post('/register', json=payload)
    assert response.json()['msg'] == 'User registered successfully'

    # login
    login_response = await client.post('/login', json=payload)
    token = login_response.cookies.get('access_token')
    assert 'access_token' in login_response.cookies

    # logout
    logout_response = await client.post('/logout', headers={'Authorization': f'Bearer {token}'})
    assert logout_response.status_code == 200
    assert logout_response.json()['msg'] == 'Logged out successfully'

    set_cookie_header = logout_response.headers.get('set-cookie', '')
    assert set_cookie_header != '', 'Set-Cookie header should be present'

    assert 'access_token=' in set_cookie_header
    assert 'Max-Age=0' in set_cookie_header or 'expires=' in set_cookie_header.lower()

    # Check that the cookie has been deleted
    assert 'access_token' not in logout_response.cookies
