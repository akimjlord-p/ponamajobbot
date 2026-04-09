from __future__ import annotations

import logging
from pathlib import Path


_IS_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    global _IS_CONFIGURED
    if _IS_CONFIGURED:
        return

    log_file = Path("app.log")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    analytics_log_file = Path("ai_analytics.log")
    analytics_handler = logging.FileHandler(analytics_log_file, encoding="utf-8")
    analytics_handler.setFormatter(formatter)

    analytics_logger = logging.getLogger("services.ai_service.analytics")
    analytics_logger.setLevel(level)
    analytics_logger.handlers.clear()
    analytics_logger.addHandler(analytics_handler)
    analytics_logger.propagate = False

    _IS_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    if not _IS_CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
