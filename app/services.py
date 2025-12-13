from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app import crud
from app.models import Book, BookCopy, User, BkCopyStatus, Loan
from app.core.auth import authenticate_user, create_access_token, hash_password
from app.core.config import Settings
from app.schemas.book import LoanCreate, LoanResponse
from logging import Logger

logger = Logger(__name__)

settings=Settings()

book_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    detail='Book not found'
)

internal_error_exception = HTTPException(
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail='An internal error occured'
)

book_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='Book with this title or ISBN already exists'
)

user_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='User with this email already exists'
)

book_copy_integrity_exception = HTTPException(
    status.HTTP_409_CONFLICT,
    detail='Error creating book copies'
)

def generate_book_copy_barcode(base_barcode, serial):
    try:
        str_serial = str(serial).zfill(3)
        return f'COPY-{base_barcode}-{str_serial}'
    except ValueError as e:
        logger.warning(f'ValueError: {e}')

# tested
async def create_new_book_service(db: AsyncSession, book_data: dict):
    try:
        book = Book(**book_data)
        await crud.create_new_book(db, book)
        logger.info(f'New book created: {book_data['title']}')
    except IntegrityError as e:
        logger.warning(f'Integrity error creating book: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error creating new book: {e}')
        await db.rollback()   
        raise internal_error_exception

# tested
async def get_book_by_isbn_service(
        db: AsyncSession, 
        isbn: int):
    try:
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        
        logger.info(f'Retrieved book: {book.library_barcode}')
        return book
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error retrieving book: {e}')
        await db.rollback()
        raise internal_error_exception

#tested  
async def update_book_service(
        db: AsyncSession,
        update_data: dict,
        isbn: int):
    try:
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        await crud.update_book(db, book, update_data)
        logger.info(f'Book-{book.library_barcode} updated')
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f'Integrity error updating book: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error updating book: {e}')
        await db.rollback()
        raise internal_error_exception

# tested
async def add_book_copies_service(db: AsyncSession, quantity: int, isbn: int):
    try:
        book_copies = []
        last_serial = 0
        book = await crud.get_book_by_isbn(db, isbn)
        if not book:
            raise book_not_found_exception
        book_lib_barcode = str(book.library_barcode)
        # get last bookcopy where isbn == book.isbn
        last_book_copy = await crud.get_last_book_copy(db, book)
        if last_book_copy:
            last_serial = last_book_copy.serial
        for i in range(quantity):
            bk_copy_serial = last_serial+1
            barcode = generate_book_copy_barcode(book_lib_barcode, bk_copy_serial)
            book_copy = BookCopy(book_isbn=isbn, serial=bk_copy_serial, copy_barcode=barcode)
            book_copies.append(book_copy)
            last_serial+=1
        await crud.add_book_copies(db, book_copies)
        logger.info(f'Created {quantity} copies of {isbn}')
        return {'message': f'{quantity} copies of ISBN-{isbn} were created successfully'}
    except IntegrityError as e:
        await db.rollback()
        logger.warning(f'Integrity error creating book copies: {e}')
        raise book_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error adding book copies: {e}')
        await db.rollback()
        raise internal_error_exception

# tested   
async def loan_book_service(
        db: AsyncSession,
        isbn: int,
        current_user: User
        ):
    try:
        user_loans = await crud.get_user_active_loans(db, current_user.id)
        if len(user_loans) >= 3:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail='User is not eligble for anymore loans'
            )
        book_copy = await crud.get_book_copy(db, isbn)
        if not book_copy:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f'There are no available copies of ISBN-{isbn} currently'
            )
        loan_data = {
            'user_id': current_user.id,
            'bk_copy_barcode': book_copy.copy_barcode
        }
        loan = Loan(**loan_data)
        created_loan = await crud.create_loan(db, loan)
        updated_bk_copy = await crud.update_bk_copy(
            db, book_copy, {'status': BkCopyStatus.BORROWED})

        logger.info('Retrieved book copy')
        return {'loan': created_loan, 'book_copy': updated_bk_copy}
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail='Loan with this id already exists'
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error fetching book_copy: {e}')
        await db.rollback()
        raise internal_error_exception

# tested 
async def create_user_service(
        db: AsyncSession,
        user_data: dict
        ):
    try:
        data = user_data.copy()
        data['password'] = hash_password(data['password'])
        await crud.create_new_user(db, User(**data))
        logger.info('Created new user successfully')
        return {'message': 'User created successfully'}
    except IntegrityError as e:
        logger.warning(f'Integrity error creating new user: {e}')
        raise user_integrity_exception
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f'DataBase error creating user: {e}')
        await db.rollback()
        raise internal_error_exception

# tested  
async def login_user_service(
        db: AsyncSession,
        user_data: dict
        ):
    try:
        ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=settings.access_token_expire_minutes)
        user = await authenticate_user(user_data, db)
        data = {'sub': user.email}
        token = create_access_token(data, ACCESS_TOKEN_EXPIRE_MINUTES)
        return {'access_token': token, 'token_type': 'bearer'}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error reading user: {e}')
        raise internal_error_exception
    
async def get_all_non_staff_users_service(
        db: AsyncSession
        ):
    try:
        users = await crud.get_all_non_staff_users(db)
        return users
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error fetching users: {e}')
        raise internal_error_exception

async def return_book_loan_service(
        db: AsyncSession,
        bk_copy_barcode_: str,
        loan_id: str
        ):
    try:
        loan = await crud.get_loan_by_id(db, loan_id)
        if not loan:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail='Loan not found'
            )
        
        # I'll fix this later
        if bk_copy_barcode_ != loan.bk_copy_barcode:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail='Book-copy-barcode not the same as stated by loan'
            )
        
        book_returned = await crud.get_book_copy_by_barcode(db, bk_copy_barcode_)
        if not book_returned:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail='Book copy not found'
            )
        updated_bk_copy = await crud.update_bk_copy(
            db, book_returned, {'status': BkCopyStatus.IN_CHECK})
        
        updated_loan = await crud.update_loan(db, loan, {'status': 'RETURNED'})
        return {'message': 'User loan cleared, awaiting staff checkup'}
    except HTTPException:
        print('its here')
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'DataBase error clearing loan: {e}')
        raise internal_error_exception