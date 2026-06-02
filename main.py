from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from database import engine, Base, async_session
from models import Habit, User
from sqlalchemy import select
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from auth import hash_password, verify_password, create_access_token, decode_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None

class HabitUpdate(BaseModel):
    name: str = None
    description: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Невалидный токен")
        return username
    except:
        raise HTTPException(status_code=401, detail="Невалидный токен")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/habits")
async def create_habit(habit: HabitCreate,  current_user: str = Depends(get_current_user)):
    async with async_session() as session:
        new_habit = Habit(name = habit.name, description = habit.description)
        session.add(new_habit)
        await session.commit()
        await session.refresh(new_habit)
        return new_habit

@app.get("/habits")
async def get_habits(current_user: str = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(Habit))
        habits = result.scalars().all()
        return habits

@app.get("/habits/{habit_id}")
async def get_habit(habit_id: int,  current_user: str = Depends(get_current_user)):
    async with async_session() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            return {"error": "Привычка не найдена"}
        else:
            return habit

@app.delete("/habits/{habit_id}")
async def delete_habit(habit_id: int,  current_user: str = Depends(get_current_user)):
    async with async_session() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            return {"error": "Привычка не найдена"}
        else:
            await session.delete(habit)
            await session.commit()
            return {"message": f"Привычка {habit_id} удалена"}

@app.put("/habits/{habit_id}")
async def update_habit(habit_id: int, data: HabitUpdate,  current_user: str = Depends(get_current_user)):
    async with async_session() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            return {"error": "Привычка не найдена"}
        else:
            if data.name:
                habit.name = data.name
            if data.description:
                habit.description = data.description
            await session.commit()
            await session.refresh(habit)
            return habit

@app.post("/register")
async def register(user: UserCreate):
    async with async_session() as session:
        new_user = User(username=user.username, hashed_password=hash_password(user.password))
        session.add(new_user)
        await session.commit()
        return {"message": f"Пользователь {user.username} создан"}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        token = create_access_token({"sub": user.username})
        return {"access_token": token, "token_type": "bearer"}
