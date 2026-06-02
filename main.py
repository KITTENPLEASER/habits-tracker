from typing import Optional

from fastapi import FastAPI
from database import engine, Base, async_session
from models import Habit
from sqlalchemy import select
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None

class HabitUpdate(BaseModel):
    name: str = None
    description: Optional[str] = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/habits")
async def create_habit(habit: HabitCreate):
    async with async_session() as session:
        new_habit = Habit(name = habit.name, description = habit.description)
        session.add(new_habit)
        await session.commit()
        await session.refresh(new_habit)
        return new_habit

@app.get("/habits")
async def get_habits():
    async with async_session() as session:
        result = await session.execute(select(Habit))
        habits = result.scalars().all()
        return habits

@app.get("/habits/{habit_id}")
async def get_habit(habit_id: int):
    async with async_session() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            return {"error": "Привычка не найдена"}
        else:
            return habit

@app.delete("/habits/{habit_id}")
async def delete_habit(habit_id: int):
    async with async_session() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            return {"error": "Привычка не найдена"}
        else:
            await session.delete(habit)
            await session.commit()
            return {"message": f"Привычка {habit_id} удалена"}

@app.put("/habits/{habit_id}")
async def update_habit(habit_id: int, data: HabitUpdate):
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
