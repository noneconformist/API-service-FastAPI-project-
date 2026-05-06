import pytest


@pytest.mark.asyncio
async def test_successful_registration(client, random_email):
    email = random_email
    payload = {'email': email, 'password': 'StrongPass123!'}

    response = await client.post('/register', json=payload)

    assert response.status_code == 200

    data = response.json()
    assert 'msg' in data
    assert data['msg'] == 'User registered successfully'
