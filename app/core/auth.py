from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from app.core.config import Settings
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud
from app.core.database import get_session
from passlib.context import CryptContext

settings = Settings()

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='users/login')
ALGORITHM = settings.hash_algorithm
SECRET_KEY = settings.secret_key

credentials_exception = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload

async def get_current_user(
        token: str=Depends(oauth2_scheme), 
        db: AsyncSession=Depends(get_session)
        ):
    token_expire_exception = HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Token has expired. Please login again'
        )
    try:
        payload = decode_token(token)
        email = payload.get('sub')
        if not email:
            raise token_expire_exception
        user = await crud.get_user_by_email(db, email)
        if not user:
            raise credentials_exception
        return user
    except ExpiredSignatureError:
        raise token_expire_exception
    except JWTError as e:
        print(f'JWTError: {e}')
        raise credentials_exception
    
async def authenticate_user(
        credentials: dict,
        db: AsyncSession=Depends(get_session)
        ):
    user_password = credentials['password']
    user_email = credentials['email']
    
    user = await crud.get_user_by_email(db, user_email)
    if not user or not verify_password(user_password, str(user.password)):
        raise credentials_exception
    return user

async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Inactive user'
        )
    return current_user

async  def get_current_staff_user(current_user=Depends(get_current_active_user)):
    if not current_user.is_staff:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail='Not enough previliges'
        )
    return current_user