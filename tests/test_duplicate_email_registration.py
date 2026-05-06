import pytest


@pytest.mark.asyncio
async def test_duplicate_email_registration(client, random_email):
    email = random_email
    payload = {'email': email, 'password': 'StrongPass123!'}

    # The first registration must be successful.
    first_response = await client.post('/register', json=payload)
    assert first_response.status_code == 200
    assert first_response.json()['msg'] == 'User registered successfully'

    # Re-registering with the same email should return an error.
    second_response = await client.post('/register', json=payload)
    assert second_response.status_code == 400

    data = second_response.json()
    assert 'detail' in data
    assert data['detail'] == 'Email already registered'
