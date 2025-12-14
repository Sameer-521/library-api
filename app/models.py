from app.core.database import Base
from sqlalchemy import (Column, String, Integer, ARRAY,
                        DateTime, Boolean, func, ForeignKey,
                        JSON, Enum)
from sqlalchemy.orm import relationship, Mapped, mapped_column
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
    return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=7)

class LoanStatus(enum.Enum):
    ACTIVE = 'active'
    RETURNED = 'returned'
    RETURNED_LATE = 'returned_late'

class Event(enum.Enum):
    CREATE_BOOK = 'create_book'
    CHECKOUT = 'checkout'
    RETURN = 'return'

class BkCopyStatus(enum.Enum):
    AVAILABLE = 'available'
    LOST = 'lost'
    BORROWED = 'borrowed'
    IN_CHECK = 'in-check'

class Book(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    isbn: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    library_barcode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, default=generate_barcode)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    location: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    #phsyical_copies = relationship()

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    card_number: Mapped[str] = mapped_column(String(50), unique=True, default=generate_library_cardnumber)
    fine_balance: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    loans = relationship('Loan', back_populates='user')

class Loan(Base):
    __tablename__ = 'loans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[str] = mapped_column(String(50), unique=True,default=generate_loan_id)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    bk_copy_barcode: Mapped[str] = mapped_column(String, ForeignKey('book_copies.copy_barcode'), index=True)
    status: Mapped[enum.Enum] = mapped_column(Enum(LoanStatus), default=LoanStatus.ACTIVE)
    checked_out_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=default_loan_due_date)
    returned_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    user = relationship('User', back_populates='loans')

class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_isbn: Mapped[str] = mapped_column(String(50), ForeignKey('books.isbn'), nullable=False, index=True)
    serial: Mapped[int] = mapped_column(Integer, nullable=False)
    copy_barcode: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[enum.Enum] = mapped_column(Enum(BkCopyStatus), default=BkCopyStatus.AVAILABLE)

class Audit(Base):
    __tablename__ = 'audit'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(50), nullable=False)
    event: Mapped[enum.Enum] = mapped_column(Enum(Event), nullable=False)
    details: Mapped[JSON] = mapped_column(JSON, nullable=False)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

