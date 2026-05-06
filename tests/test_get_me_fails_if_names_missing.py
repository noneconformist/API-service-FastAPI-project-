import pytest


@pytest.mark.asyncio
async def test_get_me_fails_if_names_missing(client, create_user):
    # Create user
    user = await create_user(
        email='nameless@foxminded.com', password='NoNamePass123!', is_superuser=False
    )
    # Check that the fields are actually empty.
    assert user.first_name is None
    assert user.last_name is None

    # Login as user
    response = await client.post('/login', json={'email': user.email, 'password': 'NoNamePass123!'})
    assert response.status_code == 200
    token = response.json()['access_token']

    # Requesting a /me profile
    response = await client.get('/me', headers={'Authorization': f'Bearer {token}'})

    # Check that error 400 was returned.
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == 'Profile data incomplete: first_name and last_name required'
