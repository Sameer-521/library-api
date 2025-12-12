import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base, get_session
from app.core.config import Settings
from app.main import app

# test db engine
test_engine = create_async_engine(Settings.test_database_url, echo=True)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

@pytest.fixture(scope='session')
async def anyio_backend():
    return 'asyncio'
