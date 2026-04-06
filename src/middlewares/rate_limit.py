import datetime
import os

import redis
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

REQUEST_LIMIT_PER_MINUTE = int(os.getenv("REQUEST_LIMIT_PER_MINUTE", "20"))
RATE_LIMIT_PREFIX = os.getenv("RATE_LIMIT_PREFIX", "rate")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

_EXEMPT_PATHS = {"/health"}

_redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def _get_ident_from_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        claims = jwt.get_unverified_claims(token)
        return claims.get("sub") or claims.get("user_id") or claims.get("id")
    except Exception:
        return None


def _get_ident_from_ip(request: Request) -> str:
    try:
        return request.client.host if request.client else "unknown"
    except Exception:
        return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        ident = _get_ident_from_token(request)
        if not ident:
            ident = _get_ident_from_ip(request)

        now = datetime.datetime.utcnow()
        key = f"{RATE_LIMIT_PREFIX}:{ident}:{now.strftime('%Y%m%d%H%M')}"

        try:
            pipe = _redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, 59)
            result = pipe.execute()
            request_number = int(result[0])
        except Exception:
            return await call_next(request)

        if request_number > REQUEST_LIMIT_PER_MINUTE:
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

        return await call_next(request)