from fastapi import APIRouter, status, Depends, Query, Form
from app.schemas.book import (BookCreate, BookResponse,
                               BookUpdate, BookCopyForm, 
                               BkCopyLoanResponse, LoanReturnForm,
                               FullScheduleInfo)
from app import services
from app.core.database import get_session, AsyncSession
from app.core.auth import get_current_active_user, get_current_staff_user
from app.models import User
from typing import Annotated

books_router = APIRouter(prefix='/books')

@books_router.get('')
async def get_all_books():
    return {'books': []}

# tested
@books_router.get('/', response_model=BookResponse)
async def get_book_by_ISBN(
    isbn: Annotated[int, Query()],
    db: AsyncSession=Depends(get_session),
    current_user: User=Depends(get_current_active_user)
    ):
    book = await services.get_book_by_isbn_service(db, isbn)
    return book

# tested
@books_router.post('', status_code=status.HTTP_201_CREATED)
async def create_book(
    book_create: Annotated[BookCreate, Form()],
    db: AsyncSession=Depends(get_session),
    staff_user=Depends(get_current_staff_user)
    ):
    book_data = book_create.model_dump()
    await services.create_new_book_service(db, book_data)
    return {'message': 'Created new book successully'}

# tested
@books_router.put('/{isbn}', status_code=status.HTTP_204_NO_CONTENT)
async def update_book(
    isbn: int,
    update_data: Annotated[BookUpdate, Form()],
    db: AsyncSession=Depends(get_session),
    staff_user=Depends(get_current_staff_user)
    ):
    book_update_data = update_data.model_dump(exclude_unset=True)
    await services.update_book_service(db, book_update_data, isbn)

# tested
@books_router.post('/generate-copies', status_code=status.HTTP_201_CREATED)
async def add_book_copies(
    add_copies_form: Annotated[BookCopyForm, Form()],
    db: AsyncSession=Depends(get_session),
    staff_user=Depends(get_current_staff_user)
    ):
    data = add_copies_form.model_dump()
    message = await services.add_book_copies_service(db, **data)
    return message

@books_router.delete('/')
async def delete_book():
    pass

@books_router.post('/loan-return')
async def return_book_loan(
    return_loan_form: Annotated[LoanReturnForm, Form()],
    db: AsyncSession=Depends(get_session),
    staff_user=Depends(get_current_staff_user),
    ):
    data = return_loan_form.model_dump()
    message = await services.return_book_loan_service(db, data['bk_copy_barcode'], data['loan_id'])
    return message

# tested
@books_router.post('/loan/{isbn}', response_model=BkCopyLoanResponse)
async def loan_book(
    isbn: int,
    db: AsyncSession=Depends(get_session),
    current_user: User=Depends(get_current_active_user)
    ):
    loan_info = await services.loan_book_service(db, isbn, current_user)
    return loan_info

@books_router.post('/book-schedule/{isbn}', 
response_model=FullScheduleInfo, status_code=status.HTTP_201_CREATED)
async def schedule_book(
    isbn: int,
    db: AsyncSession=Depends(get_session),
    current_user: User=Depends(get_current_active_user)
    ):
    schedule_info = await services.schedule_book_copy_service(db, isbn, current_user)
    return schedule_info