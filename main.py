from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_access_token, decode_token, hash_password, verify_password
from database import Base, engine, get_db
from models import Task, User

BASE_DIR = Path(__file__).resolve().parent


# ---------- Схемы ----------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[\w.-]+$")
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    done: Optional[bool] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    done: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Приложение ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="To-Do List API", lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
DB = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(db: DB, token: str = Depends(oauth2_scheme)) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный или просроченный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = int(decode_token(token)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    user = await db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_own_task(task_id: int, db: DB, user: CurrentUser) -> Task:
    task = await db.get(Task, task_id)
    # Чужая задача выглядит как несуществующая — не раскрываем, что такой id есть
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


OwnTask = Annotated[Task, Depends(get_own_task)]


# ---------- Фронтенд ----------

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(BASE_DIR / "index.html")


# ---------- Авторизация ----------

@app.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserCreate, db: DB):
    user = User(username=data.username, hashed_password=hash_password(data.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Такой пользователь уже существует")
    await db.refresh(user)
    return user


@app.post("/login", response_model=Token)
async def login(db: DB, form_data: OAuth2PasswordRequestForm = Depends()):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    return Token(access_token=create_access_token(str(user.id)))


@app.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user


# ---------- Задачи ----------

@app.get("/tasks", response_model=list[TaskOut])
async def list_tasks(db: DB, user: CurrentUser):
    result = await db.execute(
        select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc(), Task.id.desc())
    )
    return result.scalars().all()


@app.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(data: TaskCreate, db: DB, user: CurrentUser):
    title = data.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Название не может быть пустым")
    task = Task(title=title, user_id=user.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(data: TaskUpdate, task: OwnTask, db: DB):
    if data.title is not None:
        title = data.title.strip()
        if not title:
            raise HTTPException(status_code=422, detail="Название не может быть пустым")
        task.title = title
    if data.done is not None:
        task.done = data.done
    await db.commit()
    await db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task: OwnTask, db: DB):
    await db.delete(task)
    await db.commit()
    return Response(status_code=204)


@app.delete("/tasks", status_code=204)
async def delete_completed(db: DB, user: CurrentUser):
    """Удаляет все выполненные задачи текущего пользователя."""
    await db.execute(delete(Task).where(Task.user_id == user.id, Task.done.is_(True)))
    await db.commit()
    return Response(status_code=204)
