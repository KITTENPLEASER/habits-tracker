FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn sqlalchemy asyncpg "python-jose[cryptography]" passlib "bcrypt==4.0.1" python-multipart

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]