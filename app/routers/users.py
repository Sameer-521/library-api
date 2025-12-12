from datetime import timedelta
from fastapi import APIRouter, status, Depends, Query, Form
from app import services
from app.core.config import Settings
from app.core.database import get_session, AsyncSession
from typing import Annotated
from app.schemas.token import TokenResponse, Token
from app.schemas.user import UserCreate, UserLogin


users_router = APIRouter(prefix='/users')

@users_router.get('')
async def get_all_users():
    pass

@users_router.post('/sign-up', status_code=status.HTTP_201_CREATED)
async def create_new_user(
    form_data: Annotated[UserCreate, Form()],
    db: AsyncSession=Depends(get_session)
    ):
    return await services.create_user_service(db, form_data.model_dump())

@users_router.post('/login', response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[UserLogin, Form()],
    db: AsyncSession=Depends(get_session)
    ):
    return await services.login_user_service(db, form_data.model_dump())
    