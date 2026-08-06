"""密码哈希与 JWT 令牌。JWT 密钥可动态读取自数据库设置（改后全员重新登录）。"""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.settings_service import service as settings_service

_ALGO = "HS256"
_ITER = 100_000


def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITER)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def _jwt_secret(db: Session) -> str:
    return settings_service.get(db, "jwt_secret", settings.JWT_SECRET) or settings.JWT_SECRET


def create_token(db: Session, user_id: int, role: str, username: str) -> str:
    payload = {
        "uid": user_id,
        "role": role,
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, _jwt_secret(db), algorithm=_ALGO)


def decode_token(db: Session, token: str) -> dict | None:
    try:
        return jwt.decode(token, _jwt_secret(db), algorithms=[_ALGO])
    except jwt.PyJWTError:
        return None
