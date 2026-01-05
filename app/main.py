from fastapi import FastAPI
from app.core.config import Settings
from contextlib import asynccontextmanager
from app.core.middleware import AuditMiddleware
from app.routers import books, users
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.auth import create_superuser, create_mock_superuser, create_mock_user

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.test_mode == 'True':
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        
        if settings.test_mode == 'True':
            await create_mock_superuser(session)
            await create_mock_user(session)
        else:
            await create_superuser(session)
            
    yield
    await engine.dispose()
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(AuditMiddleware)

app.include_router(books.books_router)
app.include_router(users.users_router)

@app.get('/')
async def root():
    return {'message': 'This is the root page'}

# TODO:

# Write tests: ongoing
# Add maintenance utilities
# Implement soft delete functionality or just a seperate endpoint for it