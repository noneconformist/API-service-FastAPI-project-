import pytest_asyncio


@pytest_asyncio.fixture(scope='function', autouse=True)
def test_invalid_email(client):
    payload = {'email': 'not_an_email', 'password': 'StrongPass123!'}

    response = client.post('/register', json=payload)

    assert response.status_code == 422

    data = response.json()
    assert data['detail'][0]['loc'][-1] == 'email'
    assert (
        data['detail'][0]['msg']
        == 'value is not a valid email address: An email address must have an @-sign.'
    )
