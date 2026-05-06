import pytest


@pytest.mark.asyncio
async def test_short_len(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'Pss123!'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('too short' in err['msg'] for err in data['detail'])


@pytest.mark.asyncio
async def test_long_len(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'StrongPassword1234567891010!'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('too long' in err['msg'] for err in data['detail'])


@pytest.mark.asyncio
async def test_no_digit(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'StrongPass!'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('one digit' in err['msg'] for err in data['detail'])


@pytest.mark.asyncio
async def test_no_lowercase(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'STRONGPASS123!'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('one lowercase' in err['msg'] for err in data['detail'])


@pytest.mark.asyncio
async def test_no_uppercase(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'strongpassword123!'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('one uppercase' in err['msg'] for err in data['detail'])


@pytest.mark.asyncio
async def test_cannot_contain(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'StrongPass123@'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('cannot contain: @' in err['msg'] for err in data['detail'])


@pytest.mark.asyncio
async def test_special_character(client):
    payload = {'email': 'anton@foxminded.com', 'password': 'StrongPass123'}
    response = await client.post('/register', json=payload)
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data
    assert any('special character' in err['msg'] for err in data['detail'])
