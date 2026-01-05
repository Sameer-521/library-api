import pytest
import os
from httpx import AsyncClient
from dotenv import load_dotenv

load_dotenv()

mock_admin_email = os.getenv('MOCK_ADMIN_EMAIL')
mock_admin_password = os.getenv('MOCK_ADMIN_PASSWORD')
mock_admin_uid = os.getenv('MOCK_ADMIN_UID')

mock_user_email = os.getenv('MOCK_USER_EMAIL')
mock_user_password = os.getenv('MOCK_USER_PASSWORD')

BASE_URL = 'http://127.0.0.1:8000'

@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'

@pytest.fixture(scope='session')
async def client():
    async with AsyncClient(base_url=BASE_URL) as ac:
        yield ac

@pytest.fixture(scope='session')
async def auth_client(client) -> AsyncClient:
    form_data = {
        'email': mock_user_email,
        'password': mock_user_password,
    }
    response = await client.post(f'{BASE_URL}/users/login', data=form_data)
    data = response.json()
    token = data.get('access_token', None)
    client.headers.update({'Authorization': f'Bearer {token}'})
    return client

@pytest.fixture(scope='session')
async def admin_auth_client(client) -> AsyncClient:
    form_data = {
        'email': mock_admin_email,
        'password': mock_admin_password,
        'admin_uid': mock_admin_uid
    }
    response = await client.post(f'{BASE_URL}/users/admin-login', data=form_data)
    data = response.json()
    token = data.get('access_token', None)
    client.headers.update({'Authorization': f'Bearer {token}'})
    return client

@pytest.fixture(scope='function')
def book_creation_data():
    return {
        'title': 'mock1',
        'author': 'hitler',
        'location': 'a3',
        'isbn': 11223344
    }