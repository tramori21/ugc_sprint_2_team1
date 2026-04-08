import logging
from logging.handlers import DatagramHandler
from typing import cast

import logstash


class ServiceLogstashFormatter(logstash.formatter.LogstashFormatterVersion1):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> bytes:
        base = super().format(record)
        return base[:-1] + f',"service":"{self.service_name}"}}'.encode("utf-8")


class JsonDatagramHandler(DatagramHandler):
    def makePickle(self, record: logging.LogRecord) -> bytes:
        if self.formatter is None:
            raise RuntimeError("Formatter is required for JsonDatagramHandler")
        return cast(bytes, self.formatter.format(record))


def setup_logging(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    handler = JsonDatagramHandler("logstash", 5044)
    handler.setFormatter(ServiceLogstashFormatter("auth_app"))
    logger.addHandler(handler)
    return logger
