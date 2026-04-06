import logging
import os

import logstash


def setup_logging(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    host = os.getenv('LOGSTASH_HOST', '')
    port = int(os.getenv('LOGSTASH_PORT', '5044'))

    if host and not any(isinstance(handler, logstash.LogstashHandler) for handler in logger.handlers):
        logger.addHandler(logstash.LogstashHandler(host, port, version=1))

    return logger