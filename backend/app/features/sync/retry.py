"""Sync retry politikası — hangi hatanın yeniden denenip denenmeyeceğini ve backoff'u belirler.

Retry matrisi:
  - RETRY edilir : 429 (rate limit, cooldown ile) + 5xx (500/502/503/504) + ağ/timeout/connect.
  - RETRY EDİLMEZ: 401 (key), 422 (validation), 413 (payload çok büyük) — kalıcı hatalar.
Backoff: exponential, base**attempt (base=2). Üst sınır settings.target_api_max_retries (max 3).
429 sonrası ayrı bir sabit cooldown (60s) uygulanır.
"""

from __future__ import annotations

import httpx

from app.core.config import settings

# Yeniden denenebilir HTTP kodları: 429 + 5xx. 401/422/413 bilinçli olarak yok (kalıcı hata).
_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def is_retryable_status(status_code: int) -> bool:
    """HTTP status kodunun retry edilebilir olup olmadığını döner (429 veya 5xx ise True)."""
    return int(status_code) in _RETRYABLE_STATUSES


def is_retryable_exception(exc: BaseException) -> bool:
    """Ağ kaynaklı istisnaların (timeout/connect/protokol) retry edilebilir olduğunu belirler."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.ConnectError):
        return True
    return bool(isinstance(exc, httpx.RemoteProtocolError))


def should_retry(
    *,
    attempt: int,
    status_code: int | None = None,
    exc: BaseException | None = None,
) -> bool:
    """Bu denemeden sonra yeniden denenip denenmeyeceğine karar verir.

    Önce deneme üst sınırı (max_retries) kontrol edilir; aşıldıysa retry yok. İstisna verilmişse
    ağ hatası olup olmadığına, yoksa status koduna göre (429/5xx) karar verilir.
    """
    if attempt >= settings.target_api_max_retries:
        return False  # Deneme üst sınırına ulaşıldı → daha fazla denenmez.
    if exc is not None:
        return is_retryable_exception(exc)
    if status_code is None:
        return False
    return is_retryable_status(int(status_code))


def compute_backoff(attempt: int) -> float:
    """Exponential backoff süresini (saniye) döner: base**attempt (base genelde 2, attempt >= 1)."""
    base = float(settings.target_api_backoff_base_seconds)
    return float(base ** max(attempt, 1))


def cooldown_after_rate_limit() -> float:
    """429 (rate limit) sonrası uygulanan sabit bekleme süresini (varsayılan 60s) döner."""
    return float(settings.target_api_rate_limit_cooldown_seconds)
