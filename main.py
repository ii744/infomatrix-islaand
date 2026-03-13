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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Невалідний токен")
    except Exception:
        raise HTTPException(status_code=401, detail="Помилка авторизації")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Користувача не знайдено")
    return user

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Time Bank API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
@app.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Цей Email вже зареєстровано")
    
    hashed_password = pwd_context.hash(user.password)
    
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        location=user.location
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Ура! Користувача створено", "user_id": new_user.id}

SECRET_KEY = "super_secret" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/login", response_model=schemas.Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неправильний email або пароль")
    
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
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
    if current_user.id == data.to_user_id:
        raise HTTPException(status_code=400, detail="Бро, не можна переказувати час самому собі")
    if current_user.balance - data.amount < -5:
        raise HTTPException(status_code=400, detail="Недостатньо годин на балансі")

    recipient = db.query(models.User).filter(models.User.id == data.to_user_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Отримувача не знайдено")

    try:
        current_user.balance -= data.amount
        recipient.balance += data.amount
    
        new_transaction = models.Transaction(
            from_user_id=current_user.id,
            to_user_id=recipient.id,
            amount=data.amount
        )
        
        db.add(new_transaction)
        db.commit()
        
        return {"message": "Переказ успішний", "new_balance": current_user.balance}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Помилка при проведенні транзакції")
    
@app.get("/stats")
def get_user_stats(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    spent = db.query(models.Transaction).filter(models.Transaction.from_user_id == current_user.id).all()
    total_spent = sum(t.amount for t in spent)
    earned = db.query(models.Transaction).filter(models.Transaction.to_user_id == current_user.id).all()
    total_earned = sum(t.amount for t in earned)
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
    if location:
        query = query.filter(models.Request.location == location)
    if category:
        query = query.filter(models.Request.category == category)
        
    return query.order_by(models.Request.created_at.desc()).all()

@app.post("/requests")
def create_request(req: schemas.RequestCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.balance < req.time_cost:
        raise HTTPException(status_code=400, detail="Недостатньо годин на балансі для створення цього завдання")
        
    new_request = models.Request(**req.dict(), author_id=current_user.id)
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@app.patch("/requests/{request_id}/complete")
def complete_request(request_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    request = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")
        
    if request.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Тільки автор може підтвердити виконання")
        
    if request.status != models.RequestStatus.in_progress:
        raise HTTPException(status_code=400, detail="Завдання ще не в процесі виконання")

    try:
        request.status = models.RequestStatus.completed
        volunteer = db.query(models.User).filter(models.User.id == request.volunteer_id).first()

        current_user.balance -= request.time_cost
        volunteer.balance += request.time_cost
        new_transaction = models.Transaction(
            from_user_id=current_user.id,
            to_user_id=volunteer.id,
            amount=request.time_cost
        )
        
        db.add(new_transaction)
        db.commit()
        
        return {"message": "Завдання успішно закрито, години переказано волонтеру!"}
        
    except Exception as e:
        db.rollback()
        print(f"КРИТИЧНА ПОМИЛКА: {e}") 
        raise HTTPException(status_code=500, detail="Помилка при проведенні транзакції")
    
@app.post("/responses")
def create_response(
    res: schemas.ResponseCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    request = db.query(models.Request).filter(models.Request.id == res.request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")
    if request.author_id == current_user.id:
        raise HTTPException(status_code=400, detail="Ви не можете відгукнутися на власне завдання")
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
    response = db.query(models.Response).filter(models.Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Відгук не знайдено")

    request = db.query(models.Request).filter(models.Request.id == response.request_id).first()
    if request.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Тільки автор може обирати виконавця")
    
    response.status = models.ResponseStatus.accepted
    request.status = models.RequestStatus.in_progress
    request.volunteer_id = response.volunteer_id
    other_responses = db.query(models.Response).filter(
        models.Response.request_id == request.id, 
        models.Response.id != response.id
    ).all()
    
    for r in other_responses:
        r.status = models.ResponseStatus.rejected
        
    db.commit()
    
    return {"message": "Виконавця обрано! Завдання тепер в статусі 'У процесі'."}

@app.get("/users/me/requests")
def get_my_requests(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    my_requests = db.query(models.Request).filter(models.Request.author_id == current_user.id).order_by(models.Request.created_at.desc()).all()
    return my_requests