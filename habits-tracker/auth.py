import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

logger = logging.getLogger(__name__)

# Секрет берётся из окружения и никогда не хранится в репозитории.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    logger.warning("SECRET_KEY не задан — сгенерирован временный, токены сбросятся после перезапуска")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))


def _encode(password: str) -> bytes:
    # bcrypt учитывает только первые 72 байта пароля
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Бросает jwt.PyJWTError, если токен невалиден или истёк."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
