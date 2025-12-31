from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import Settings
from contextlib import asynccontextmanager
from functools import lru_cache
from app.core.middleware import AuditMiddleware
from app.routers import books, users
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.auth import create_superuser

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await create_superuser(session)
    yield
    await engine.dispose()

@lru_cache
async def get_settings():
    settings = Settings()
    return settings
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(AuditMiddleware)

app.include_router(books.books_router)
app.include_router(users.users_router)

@app.get('/')
async def root():
    await get_settings()
    return {'message': 'This is the root page'}

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     request.state.exception = exc
#     raise exc

# TODO:

# Implement audit logic: testing phase
# Implement book copy clearance: check book status and mark them accordingly e.g lost
# Implement book clearance via external worker
# Add maintenance utilities
# seperate admin login from public user login endpoint