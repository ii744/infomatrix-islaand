from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas
from database import engine, SessionLocal
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

# Це вказує FastAPI, де шукати токен (у заголовку Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Функція, яка перевіряє токен і повертає поточного користувача


# Функція-провайдер: видає сесію бази даних для кожного запиту
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        # Розшифровуємо токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Невалідний токен")
    except Exception:
        raise HTTPException(status_code=401, detail="Помилка авторизації")
    
    # Шукаємо юзера в базі за ID з токена
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Користувача не знайдено")
    return user

# Створюємо таблиці, якщо їх ще немає
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Time Bank API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # На хакатоні дозволяємо всім, щоб не було проблем
    allow_credentials=True,
    allow_methods=["*"], # Дозволяємо GET, POST, PATCH тощо
    allow_headers=["*"],
)

# Налаштування для хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# НАШ ПЕРШИЙ ЕНДПОІНТ: Реєстрація
@app.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Перевіряємо, чи немає вже такого email в базі
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Цей Email вже зареєстровано")
    
    # 2. Шифруємо пароль
    hashed_password = pwd_context.hash(user.password)
    
    # 3. Створюємо об'єкт нового користувача (баланс 2 години підтягнеться сам!)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        location=user.location
    )
    
    # 4. Зберігаємо в базу (робимо commit транзакції)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Оновлюємо об'єкт, щоб отримати згенерований ID
    
    return {"message": "Ура! Користувача створено", "user_id": new_user.id}

# Налаштування для токена (для хакатону залишаємо так, в реальному житті це ховають у .env)
SECRET_KEY = "super_secret_hackathon_key_for_sashko" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Токен "згорить" через годину

# Допоміжна функція: друкує сам бейдж (токен)
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# НАШ ДРУГИЙ ЕНДПОІНТ: Вхід у систему (Логін)
@app.post("/login", response_model=schemas.Token)
def login_user(
    # Замінюємо schemas.UserLogin на OAuth2PasswordRequestForm
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # Тепер замість user_credentials.email пишемо form_data.username
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неправильний email або пароль")
    
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    # Ми просто повертаємо об'єкт користувача, якого знайшла "Охорона"
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "balance": current_user.balance,
        "location": current_user.location
    }

@app.post("/transfer")
def transfer_time(
    data: schemas.TransferTime, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Перевіряємо, чи не намагається юзер переказати час самому собі
    if current_user.id == data.to_user_id:
        raise HTTPException(status_code=400, detail="Не можна переказувати час самому собі")

    # 2. Перевіряємо баланс (дозволяємо невеликий мінус, наприклад до -5 годин)
    if current_user.balance - data.amount < -5:
        raise HTTPException(status_code=400, detail="Недостатньо годин на балансі")

    # 3. Шукаємо отримувача
    recipient = db.query(models.User).filter(models.User.id == data.to_user_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Отримувача не знайдено")

    try:
        # ПОЧАТОК ТРАНЗАКЦІЇ
        # Віднімаємо у відправника
        current_user.balance -= data.amount
        # Додаємо отримувачу
        recipient.balance += data.amount
        
        # Створюємо запис про транзакцію для історії
        new_transaction = models.Transaction(
            from_user_id=current_user.id,
            to_user_id=recipient.id,
            amount=data.amount
        )
        
        db.add(new_transaction)
        db.commit() # Зберігаємо всі зміни одночасно!
        
        return {"message": "Переказ успішний", "new_balance": current_user.balance}
        
    except Exception as e:
        db.rollback() # Якщо щось пішло не так — скасовуємо ВСІ зміни
        raise HTTPException(status_code=500, detail="Помилка при проведенні транзакції")
    
@app.get("/stats")
def get_user_stats(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Рахуємо витрачений час (де я був відправником)
    spent = db.query(models.Transaction).filter(models.Transaction.from_user_id == current_user.id).all()
    total_spent = sum(t.amount for t in spent)

    # 2. Рахуємо отриманий час (де я був отримувачем)
    earned = db.query(models.Transaction).filter(models.Transaction.to_user_id == current_user.id).all()
    total_earned = sum(t.amount for t in earned)

    # 3. Беремо останні 10 транзакцій для списку історії
    history = db.query(models.Transaction).filter(
        or_(
            models.Transaction.from_user_id == current_user.id,
            models.Transaction.to_user_id == current_user.id
        )
    ).order_by(models.Transaction.created_at.desc()).limit(10).all()

    return {
        "current_balance": current_user.balance,
        "total_spent": total_spent,
        "total_earned": total_earned,
        "history": history
    }

@app.get("/requests")
def get_requests(location: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Request).filter(models.Request.status == models.RequestStatus.open)
    
    # Фільтри, як і просив напарник
    if location:
        query = query.filter(models.Request.location == location)
    if category:
        query = query.filter(models.Request.category == category)
        
    return query.order_by(models.Request.created_at.desc()).all()

# 2. Створити нове завдання
@app.post("/requests")
def create_request(req: schemas.RequestCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Перевіряємо, чи є в людини достатньо годин, щоб просити про допомогу!
    if current_user.balance < req.time_cost:
        raise HTTPException(status_code=400, detail="Недостатньо годин на балансі для створення цього завдання")
        
    new_request = models.Request(**req.dict(), author_id=current_user.id)
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

# 3. Підтвердження виконання завдання (Транзакція часу!)
@app.patch("/requests/{request_id}/complete")
def complete_request(request_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Шукаємо завдання
    request = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")
        
    # Тільки автор завдання може його закрити
    if request.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Тільки автор може підтвердити виконання")
        
    # Якщо воно ще не в роботі
    if request.status != models.RequestStatus.in_progress:
        raise HTTPException(status_code=400, detail="Завдання ще не в процесі виконання")

    try:
        # ПОЧАТОК ТРАНЗАКЦІЇ (як ми робили раніше)
        request.status = models.RequestStatus.completed
        
        # Знаходимо волонтера
        volunteer = db.query(models.User).filter(models.User.id == request.volunteer_id).first()
        
        # Переказуємо години!
        current_user.balance -= request.time_cost
        volunteer.balance += request.time_cost
        
        # Записуємо в історію
        # Записуємо в історію (БЕЗ request_id)
        new_transaction = models.Transaction(
            from_user_id=current_user.id,
            to_user_id=volunteer.id,
            amount=request.time_cost
        )
        
        db.add(new_transaction)
        db.commit() # Зберігаємо всі зміни одночасно
        
        return {"message": "Завдання успішно закрито, години переказано волонтеру!"}
        
    except Exception as e:
        db.rollback()
        print(f"КРИТИЧНА ПОМИЛКА: {e}") # Тепер ти побачиш причину в терміналі!
        raise HTTPException(status_code=500, detail="Помилка при проведенні транзакції")
    
@app.post("/responses")
def create_response(
    res: schemas.ResponseCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Перевіряємо, чи існує таке завдання
    request = db.query(models.Request).filter(models.Request.id == res.request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    # Не можна відгукнутися на своє ж завдання
    if request.author_id == current_user.id:
        raise HTTPException(status_code=400, detail="Ви не можете відгукнутися на власне завдання")

    # Створюємо відгук
    new_response = models.Response(
        request_id=res.request_id,
        volunteer_id=current_user.id,
        message=res.message
    )
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    
    return {"message": "Ви успішно відгукнулися на завдання!", "response_id": new_response.id}

@app.get("/requests/{request_id}/responses")
def get_request_responses(request_id: str, db: Session = Depends(get_db)):
    responses = db.query(models.Response).filter(models.Response.request_id == request_id).all()
    return responses

@app.patch("/responses/{response_id}/accept")
def accept_response(
    response_id: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Знаходимо відгук
    response = db.query(models.Response).filter(models.Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Відгук не знайдено")
        
    # Знаходимо саме завдання
    request = db.query(models.Request).filter(models.Request.id == response.request_id).first()
    
    # Тільки автор завдання може прийняти відгук
    if request.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Тільки автор може обирати виконавця")
        
    # Переводимо відгук у статус accepted
    response.status = models.ResponseStatus.accepted
    
    # Переводимо завдання у статус in_progress та призначаємо волонтера!
    request.status = models.RequestStatus.in_progress
    request.volunteer_id = response.volunteer_id
    
    # Автоматично відхиляємо всі інші відгуки на це завдання
    other_responses = db.query(models.Response).filter(
        models.Response.request_id == request.id, 
        models.Response.id != response.id
    ).all()
    
    for r in other_responses:
        r.status = models.ResponseStatus.rejected
        
    db.commit()
    
    return {"message": "Виконавця обрано! Завдання перейшло в статус 'У процесі'."}