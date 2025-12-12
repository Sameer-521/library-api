from app.core.database import Base
from sqlalchemy import (Column, String, Integer, ARRAY,
                        DateTime, Boolean, func, ForeignKey,
                        JSON, Enum)
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import string, secrets, enum

def generate_barcode(serial: str | None = None):
    digits = string.digits
    serial = ''.join([secrets.choice(digits) for _ in range(7)])
    return f'BK-{serial}'

def generate_random_id():
    digits = string.digits
    letters = string.ascii_uppercase
    letter_part = ''.join([secrets.choice(letters) for _ in range(2)])
    num_part = ''.join([secrets.choice(digits) for _ in range(8)])
    return f'{letter_part}-{num_part}'

def generate_library_cardnumber():
    id = generate_random_id()
    return f'LB-{id}'

def generate_loan_id():
    id = generate_random_id()
    return f'LN-{id}'

def default_loan_due_date():
    return datetime.now(timezone.utc) + timedelta(days=7)

class LoanStatus(enum.Enum):
    ACTIVE = 'active'
    RETURNED = 'returned'
    LOST = 'lost'
    OVERDUE = 'overdue'

class Event(enum.Enum):
    CREATE_BOOK = 'create_book'
    CHECKOUT = 'checkout'
    RETURN = 'return'

class BkCopyStatus(enum.Enum):
    AVAILABLE = 'available'
    LOST = 'lost'
    BORROWED = 'borrowed'

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), unique=True, nullable=False)
    author = Column(String(100), nullable=False)
    isbn = Column(String(50), unique=True, nullable=False)
    library_barcode = Column(String(50), unique=True, nullable=False, default=generate_barcode)
    available = Column(Boolean, default=True)
    location = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    #phsyical_copies = relationship()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    full_name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String, nullable=False)
    card_number = Column(String(50), unique=True, default=generate_library_cardnumber)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    loans = relationship('Loan', back_populates='user')

class Loan(Base):
    __tablename__ = 'loans'

    id = Column(Integer, primary_key=True)
    loan_id = Column(String(50), unique=True,default=generate_loan_id)
    user_id = Column(String, ForeignKey('users.id'))
    bk_copy_barcode = Column(String, ForeignKey('book_copies.copy_barcode'), index=True)
    status = Column(Enum(LoanStatus), default=LoanStatus.ACTIVE)
    checked_out_at = Column(DateTime(timezone=True), server_default=func.now())
    due_at = Column(DateTime(timezone=True), default=default_loan_due_date)
    returned_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship('User', back_populates='loans')

class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_id = Column(Integer, primary_key=True)
    book_isbn = Column(String(50), ForeignKey('books.isbn'), nullable=False, index=True)
    serial = Column(Integer, nullable=False)
    copy_barcode = Column(String(50), nullable=False)
    status = Column(Enum(BkCopyStatus), default=BkCopyStatus.AVAILABLE)

class Audit(Base):
    __tablename__ = 'audit'

    id = Column(Integer, primary_key=True)
    actor_id = Column(String(50), nullable=False)
    event = Column(Enum(Event), nullable=False)
    details = Column(JSON, nullable=False)
    audited_at = Column(DateTime(timezone=True), server_default=func.now())

# how to attatch loan to original book so we can track how many loans a book has had
# Book.loans = relationship('Loan', secondary='book_copies',
#                           primaryjoin=Book.id==BookCopy.book_id, secondaryjoin=BookCopy.copy_id==Loan.book_copy_id, back_populates='book')
# Loan.book = relationship('Book', back_populates='loans')
# explaining the relationships the Book.loans and Loan.book:
# A Book can have multiple Loans through its BookCopies, and each Loan is associated with a specific BookCopy of that Book.

