"""Domain exception'ları + tutarlı JSON hata yanıtı.

Yanıt formatı: { "error": { "code", "message", "detail" } }
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Tüm domain hatalarının tabanı."""

    code: str = "APP_ERROR"
    status_code: int = 400

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422


class DuplicateImportError(AppError):
    code = "DUPLICATE_IMPORT"
    status_code = 409


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class TargetApiError(AppError):
    """Hedef MES API çağrısı başarısız (auth/rate-limit/sunucu)."""

    code = "TARGET_API_ERROR"
    status_code = 502


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """AppError'ı sözleşmedeki tutarlı JSON hata gövdesine çevirir."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "detail": exc.detail}},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Tüm AppError alt sınıfları için ortak handler'ı FastAPI'ye kaydeder."""
    app.add_exception_handler(AppError, _app_error_handler)
