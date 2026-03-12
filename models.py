from sqlalchemy import Column, Integer, String, DateTime
import uuid
from datetime import datetime
from database import Base
from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_user_id = Column(String, ForeignKey("users.id"))
    to_user_id = Column(String, ForeignKey("users.id"))
    amount = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    location = Column(String)
    balance = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)

class RequestStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"

class ResponseStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

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
    
    volunteer_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    responses = relationship("Response", back_populates="request")


class Response(Base):
    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, ForeignKey("requests.id"), nullable=False)
    volunteer_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(ResponseStatus), default=ResponseStatus.pending)
    message = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("Request", back_populates="responses")
