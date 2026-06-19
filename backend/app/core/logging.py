"""Yapılandırılmış logging kurulumu. Secret ASLA log'lanmaz."""

from __future__ import annotations

import logging

from app.core.config import settings

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Kök logger'ı .env'deki LOG_LEVEL ve standart formatla yapılandırır."""
    logging.basicConfig(level=settings.log_level.upper(), format=_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Modül adına bağlı bir logger döndürür (genelde `__name__` ile çağrılır)."""
    return logging.getLogger(name)
