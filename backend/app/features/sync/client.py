"""Sync HTTP client — hedef API'ye POST; X-Production-Key header'ı + secret redaction.

Secret yalnızca .env'den (settings.target_api_key) okunur ve hiçbir zaman log'a yazılmaz;
log'larda yerine REDACTED ('***REDACTED***') basılır. Ağ/timeout hataları TransientSyncError
(retry edilir), kalıcı hatalar service katmanında PermanentSyncError olarak ele alınır.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

_logger = logging.getLogger("sync.client")

# Log'larda secret yerine basılan maskeleme metni — secret asla loglanmaz.
REDACTED: str = "***REDACTED***"


class PermanentSyncError(Exception):
    """Kalıcı (retry edilmeyen) gönderim hatası — örn. 401/422/413. Yeniden denenmez."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)
        self.message = message


class TransientSyncError(Exception):
    """Geçici (retry edilebilen) hata — ağ/timeout/connect veya 5xx. Backoff ile yeniden denenir."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)
        self.message = message


def _headers() -> dict[str, str]:
    # Secret (X-Production-Key) yalnız .env kaynaklı settings'ten alınır; koda gömülmez.
    return {
        "Content-Type": "application/json",
        "X-Production-Key": settings.target_api_key,
    }


def submit_payload(
    payload: dict[str, Any],
    idempotency_key: str,
    timeout: float | None = None,
) -> tuple[int, dict[str, Any]]:
    """Payload'ı hedef API'ye POST eder; (http_status, response_body) döner.

    Ağ/timeout/connect hatalarında TransientSyncError fırlatır (retry edilir). HTTP yanıt
    kodunun retry/permanent yorumu çağıran service katmanına bırakılır. Log'larda secret
    yerine REDACTED basılır; gerçek key asla yazılmaz.
    """
    url = settings.target_submit_url
    headers = _headers()
    # Secret redaction: hem mesajda hem extra'da key yerine REDACTED → secret log'a sızmaz.
    _logger.info(
        "sync.submit url=%s idem=%s key=%s",
        url,
        idempotency_key,
        REDACTED,
        extra={"key": REDACTED, "idempotency_key": idempotency_key},
    )
    client_timeout = timeout if timeout is not None else float(settings.target_api_timeout_seconds)
    try:
        with httpx.Client(timeout=client_timeout) as client:
            response = client.post(url, json=payload, headers=headers)
    # Ağ/timeout/genel HTTP hataları geçici sayılır → status_code=0 ile TransientSyncError;
    # service katmanı bunları retry matrisine göre yeniden dener.
    except httpx.TimeoutException as exc:
        raise TransientSyncError(0, f"timeout: {exc.__class__.__name__}") from exc
    except httpx.ConnectError as exc:
        raise TransientSyncError(0, f"connect_error: {exc.__class__.__name__}") from exc
    except httpx.HTTPError as exc:
        raise TransientSyncError(0, f"http_error: {exc.__class__.__name__}") from exc

    status = int(response.status_code)
    body: dict[str, Any]
    try:
        body = response.json()
    except ValueError:
        # JSON olmayan yanıt → ham metin (ilk 1000 karakter) saklanır.
        body = {"raw": response.text[:1000]}

    _logger.info(
        "sync.submit.response status=%s idem=%s key=%s",
        status,
        idempotency_key,
        REDACTED,
        extra={"key": REDACTED, "idempotency_key": idempotency_key, "status": status},
    )
    return status, body
