import pytest


@pytest.mark.asyncio
async def test_superuser_sorting(client, create_user):
    # Create a few users
    user1 = await create_user(
        email='walter_white@breakingbad.com', password='SortPass123!', is_superuser=False
    )
    user1.balance = 10.0

    user2 = await create_user(
        email='jesse_pinkman@breakingbad.com', password='SortPass124!', is_superuser=False
    )
    user2.balance = 20.0

    superuser = await create_user(
        email='tuko@breakingbad.com', password='AdminPass123!', is_superuser=True
    )

    # Login as superuser
    response = await client.post(
        '/login', json={'email': superuser.email, 'password': 'AdminPass123!'}
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    # Sort by email
    response = await client.get(
        '/users?sort_by=balance&direction=asc', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()

    # Check low balance first
    emails_sorted = [u['email'] for u in data]
    assert emails_sorted.index('walter_white@breakingbad.com') < emails_sorted.index(
        'jesse_pinkman@breakingbad.com'
    )

    # Sort by balance in descending order
    response = await client.get(
        '/users?sort_by=balance&direction=desc', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()

    # Check the reverse order
    emails_sorted = [u['email'] for u in data]
    assert emails_sorted.index('jesse_pinkman@breakingbad.com') < emails_sorted.index(
        'walter_white@breakingbad.com'
    )
