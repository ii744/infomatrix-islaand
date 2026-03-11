from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransactionBase(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    amount: int
    created_at: datetime

    class Config:
        from_attributes = True # Це дозволяє Pydantic працювати з моделями бази даних
# Це те, що ми чекаємо від користувача при реєстрації
class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    location: str

# Це те, що ми чекаємо від користувача при вході
class UserLogin(BaseModel):
    email: str
    password: str

# Це те, що ми віддамо йому у відповідь (його цифровий бейдж)
class Token(BaseModel):
    access_token: str
    token_type: str

class TransferTime(BaseModel):
    to_user_id: str
    amount: int


class RequestCreate(BaseModel):
    title: str
    description: str
    time_cost: int
    location: str
    category: str

# Схема для відгуку на завдання (кнопка "Відгукнутися")
class ResponseCreate(BaseModel):
    request_id: str
    message: Optional[str] = ""