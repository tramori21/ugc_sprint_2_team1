import asyncio
import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from services.consumer import consume

from core.logging import setup_logging


def setup_sentry() -> None:
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    sentry_environment = os.getenv("SENTRY_ENVIRONMENT", "local")

    if not (sentry_dsn.startswith("http://") or sentry_dsn.startswith("https://")):
        return

    sentry_sdk.init(  # type: ignore[abstract]
        dsn=sentry_dsn,
        environment=sentry_environment,
        integrations=[LoggingIntegration(level=None, event_level=None)],
        traces_sample_rate=1.0,
    )


if __name__ == "__main__":
    setup_logging("ugc_etl")
    setup_sentry()
    asyncio.run(consume())
