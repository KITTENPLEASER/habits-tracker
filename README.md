# Habits Tracker API

**REST API для отслеживания привычек с авторизацией и веб-интерфейсом.**

## Стек технологий
- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy
- Uvicorn
- JWT авторизация
- Docker + docker-compose

## Запуск через докер

```bash
git clone https://github.com/KITTENPLEASER/habits-tracker.git
cd habits-tracker
docker-compose up --build
```

## Локальный запуск

1. Необходимо установить зависимости

```bash
pip install fastapi uvicorn sqlalchemy asyncpg python-jose passlib bcrypt python-multipart
```

2. Настроить подключения к базе данных в `database.py`

3. Запустить сервер

```bash
uvicorn main:app --reload
```

4. Открыть `http://localhost:8000`

## Эндпоинты

| Метод | URL          | Описание |
|-------|--------------|----------|
| GET | /habits      | Все привычки |
| GET | /habits/{id} | Привычка по id |
| POST | /habits      | Создать привычку |
| PUT | /habits/{id} | Обновить привычку |
| DELETE | /habits/{id} | Удалить привычку |

**Докуметация: `http://localhost:8000/docs`**
