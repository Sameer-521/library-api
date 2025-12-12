from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Book, BookCopy, User, Loan
from typing import List

async def get_book_by_id(db: AsyncSession, book_id: int):
    book = await db.get(Book, book_id)
    return book

async def get_book_by_barcode(db: AsyncSession, barcode: str):
    stmt = select(Book).where(Book.library_barcode == barcode)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_book_by_isbn(db: AsyncSession, bk_isbn: int):
    stmt = select(Book).where(Book.isbn == bk_isbn)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_last_book_copy(db: AsyncSession, book: Book):
    stmt = select(BookCopy).order_by(desc(BookCopy.serial)).where(BookCopy.book_isbn == book.isbn)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_new_book(db: AsyncSession, book: Book):
    db.add(book)
    await db.commit()

async def add_book_copies(db: AsyncSession, copies: List[BookCopy]):
    db.add_all(copies)
    await db.commit()

async def update_book(
        db: AsyncSession, 
        book: Book, 
        update_data: dict,
        ):
    for key, value in update_data.items():
        setattr(book, key, value)
    await db.commit()

async def get_book_copy(
        db: AsyncSession,
        isbn: int
        ):
    stmt = select(BookCopy).where(BookCopy.book_isbn == isbn, BookCopy.status == "AVAILABLE")
    result = await db.execute(stmt)
    return result.scalars().first()

async def update_bk_copy(
        db: AsyncSession, 
        book_copy: BookCopy, 
        update_data: dict
        ):
    for key, value in update_data.items():
        setattr(book_copy, key, value)
    await db.commit()
    await db.refresh(book_copy)
    return book_copy

async def get_user_by_email(db: AsyncSession, _email: str):
    stmt = select(User).where(User.email == _email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_new_user(db: AsyncSession, user: User):
    db.add(user)
    await db.commit()

async def create_loan(db: AsyncSession, loan: Loan):
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return loan