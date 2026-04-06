import json
import os
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from uuid import uuid4

from fastapi import FastAPI, Request

from api.router import router
from core.logging import setup_logging
from core.tracing import setup_tracing
from db.mongo import close_mongo, get_database
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.request_id import RequestIdMiddleware
from services.ugc_service import UGCService

app = FastAPI(title='auth_service')

setup_tracing(app)
logger = setup_logging('auth_service')

app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware)
app.include_router(router)


def send_sentry_event(message: str) -> None:
    dsn = os.getenv('SENTRY_DSN', '').strip()
    if not dsn.startswith('http://') and not dsn.startswith('https://'):
        return

    parsed = urlparse(dsn)
    if not parsed.hostname:
        return

    public_key = parsed.username or ''
    secret_key = parsed.password or ''
    project_id = parsed.path.strip('/')

    if not public_key or not project_id:
        return

    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    store_url = f'{parsed.scheme}://{parsed.hostname}:{port}/api/{project_id}/store/'
    auth_header = (
        'Sentry '
        f'sentry_version=7, sentry_client=custom-python/1.0, '
        f'sentry_key={public_key}, sentry_secret={secret_key}'
    )
    payload = {
        'event_id': uuid4().hex,
        'message': message,
        'level': 'error',
        'logger': 'auth_service',
        'platform': 'python',
        'timestamp': datetime.utcnow().isoformat(),
        'server_name': 'auth_service',
    }

    try:
        request = UrlRequest(
            store_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'X-Sentry-Auth': auth_header,
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with urlopen(request, timeout=5) as response:
            body = response.read().decode('utf-8', errors='ignore')
            logger.error(
                'sentry store response',
                extra={
                    'status_code': response.status,
                    'response_text': body[:300],
                    'store_url': store_url,
                },
            )
    except Exception as exc:
        logger.error(
            'sentry store request failed',
            extra={'error': str(exc), 'store_url': store_url},
        )


@app.on_event('startup')
async def startup() -> None:
    await UGCService.ensure_indexes(get_database())


@app.on_event('shutdown')
async def shutdown() -> None:
    close_mongo()


@app.get('/health')
async def health():
    logger.info('health check')
    return {'status': 'ok'}


@app.get('/sentry-debug')
async def sentry_debug(request: Request):
    logger.error(
        'sentry debug endpoint failed',
        extra={
            'path': str(request.url.path),
            'method': request.method,
        },
    )
    send_sentry_event('auth sentry debug error')
    raise RuntimeError('sentry debug error')