from sqlalchemy import Column, Integer, String, DateTime
import uuid
from datetime import datetime
from database import Base
from sqlalchemy import ForeignKey # Додай цей імпорт вгору
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Хто віддає час (Замовник)
    from_user_id = Column(String, ForeignKey("users.id"))
    # Хто отримує час (Волонтер)
    to_user_id = Column(String, ForeignKey("users.id"))
    # Скільки годин переказуємо
    amount = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users" # Так таблиця буде називатися в PostgreSQL

    # Описуємо колонки
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    location = Column(String)
    balance = Column(Integer, default=2) # Ті самі стартові 2 години авансом!
    created_at = Column(DateTime, default=datetime.utcnow)

class RequestStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"

# Створюємо статуси для відгуків
class ResponseStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

# 1. ТАБЛИЦЯ ЗАВДАНЬ (Еквівалент Request.js)
class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    time_cost = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    category = Column(String, nullable=False)
    
    status = Column(Enum(RequestStatus), default=RequestStatus.open)
    
    volunteer_id = Column(String, ForeignKey("users.id"), nullable=True) # Спочатку пусте
    created_at = Column(DateTime, default=datetime.utcnow)

    # Зв'язки для зручності (щоб Python сам підтягував дані)
    responses = relationship("Response", back_populates="request")


# 2. ТАБЛИЦЯ ВІДГУКІВ (Еквівалент Response.js)
class Response(Base):
    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, ForeignKey("requests.id"), nullable=False)
    volunteer_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(ResponseStatus), default=ResponseStatus.pending)
    message = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Зв'язок назад до завдання
    request = relationship("Request", back_populates="responses")
