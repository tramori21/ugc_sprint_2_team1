from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4

from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _ts(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def _encode(data: Dict[str, Any], expires: datetime) -> str:
    now = datetime.utcnow()
    payload = dict(data)
    payload.update({'iat': _ts(now), 'exp': _ts(expires), 'jti': str(uuid4())})
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm)


def create_access_token(data: Dict[str, Any]) -> str:
    expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return _encode(data, expires)


def create_refresh_token(data: Dict[str, Any]) -> str:
    expires = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    return _encode(data, expires)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[
                settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError('Invalid token') from e

