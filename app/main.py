from fastapi import FastAPI
from app.core.config import Settings
from contextlib import asynccontextmanager
from functools import lru_cache
from app.routers import books, users
from app.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield # app runs here
    await engine.dispose()
    
app = FastAPI(lifespan=lifespan)

app.include_router(books.books_router)
app.include_router(users.users_router)

@lru_cache
async def get_settings():
    settings = Settings()
    return settings

@app.get('/')
async def root():
    await get_settings()
    return {'message': 'This is the root page'}


