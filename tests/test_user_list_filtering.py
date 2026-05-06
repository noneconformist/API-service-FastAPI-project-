import pytest
from sqlalchemy.future import select

from models import User


@pytest.mark.asyncio
async def test_superuser_filtering(client, create_user):
    # Create a few users
    user1 = await create_user(
        email='walter_white@breakingbad.com', password='FilterPass123!', is_superuser=False
    )
    user1.first_name = 'Walter'
    user2 = await create_user(
        email='jesse_pinkman@breakingbad.com', password='FilterPass124!', is_superuser=False
    )
    user2.first_name = 'Jesse'
    superuser = await create_user(
        email='gustavo@breakingbad.com', password='AdminPass123!', is_superuser=True
    )

    # Login as superuser
    response = await client.post(
        '/login', json={'email': superuser.email, 'password': 'AdminPass123!'}
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    # Filtering by first name
    response = await client.get(
        '/users?first_name=Walter', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()

    # Check that the correct user has returned.
    assert len(data) == 1
    assert data[0]['first_name'] == 'Walter'


@pytest.mark.asyncio
async def test_superuser_excludes_deleted_users(client, create_user, db_session):
    # Create 2 users
    active_user = await create_user(
        email='active_user@test.com', password='ActivePass123!', is_superuser=False
    )
    active_user.first_name = 'Active'

    deleted_user = await create_user(
        email='deleted_user@test.com', password='DeletedPass123!', is_superuser=False
    )
    deleted_user.first_name = 'Deleted'

    # Mark second user as deleted
    result = await db_session.execute(select(User).where(User.id == deleted_user.id))
    db_deleted = result.scalars().first()
    db_deleted.is_active = False
    await db_session.commit()

    # Create superuser
    superuser = await create_user(
        email='superuser@test.com', password='SuperPass123!', is_superuser=True
    )

    # Login as superuser
    response = await client.post(
        '/login', json={'email': superuser.email, 'password': 'SuperPass123!'}
    )
    assert response.status_code == 200
    token = response.json()['access_token']

    # Request a list of users
    response = await client.get('/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = response.json()

    # Check that the deleted user has not returned.
    emails = [u['email'] for u in data]
    assert active_user.email in emails
    assert deleted_user.email not in emails
