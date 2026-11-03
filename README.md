# To-Do List

Веб-приложение «Список задач» с регистрацией, REST API и сохранением задач в базе данных.

## Возможности

- Регистрация и вход (JWT). У каждого пользователя свой список задач.
- Добавление задач.
- Отметка выполненных задач (чекбокс или клик по названию).
- Удаление задачи и массовое удаление выполненных.
- Фильтры «все / активные / выполненные» и счётчик прогресса.
- Задачи хранятся в PostgreSQL, сессия — в `localStorage`, поэтому после обновления страницы всё остаётся на месте.
- Адаптивная вёрстка для телефона.

## Стек

- **Бэкенд:** Python 3.13, FastAPI, SQLAlchemy 2 (async), PostgreSQL
- **Авторизация:** JWT (PyJWT), пароли хешируются bcrypt
- **Фронтенд:** HTML, CSS, чистый JavaScript без фреймворков
- **Запуск:** Docker + docker-compose

## Запуск через Docker

```bash
git clone https://github.com/KITTENPLEASER/habits-tracker.git
cd habits-tracker
cp .env.example .env.example
docker compose up --build
```

Открыть http://localhost:8000

## Локальный запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DATABASE_URL="sqlite+aiosqlite:///./todo.db"
export SECRET_KEY="любая-длинная-случайная-строка"

uvicorn main:app --reload
```

## API

Все запросы к `/tasks` требуют заголовок `Authorization: Bearer <token>`.

| Метод  | URL             | Описание                                     |
|--------|-----------------|----------------------------------------------|
| POST   | `/register`     | Регистрация `{username, password}`           |
| POST   | `/login`        | Получить токен (form-data `username`, `password`) |
| GET    | `/me`           | Текущий пользователь                         |
| GET    | `/tasks`        | Список своих задач                           |
| POST   | `/tasks`        | Создать задачу `{title}`                     |
| PATCH  | `/tasks/{id}`   | Изменить `{title?, done?}`                   |
| DELETE | `/tasks/{id}`   | Удалить задачу                               |
| DELETE | `/tasks`        | Удалить все выполненные задачи               |

Интерактивная документация: http://localhost:8000/docs

## Использованные AI-инструменты

- **Claude (Claude Code)** — ревью кода, поиск уязвимостей, рефакторинг бэкенда и переработка интерфейса.
