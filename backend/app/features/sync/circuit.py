"""Sync circuit breaker — uzun süreli hedef API hatalarında otomatik duraklatma.

Basit, süreç-içi (in-process) breaker: ardışık `failure_threshold` başarısız gönderimden
sonra `OPEN` olur ve `cooldown_seconds` boyunca yeni gönderimleri **denemeden** reddeder.
Cooldown dolunca `half-open` — bir deneme hakkı; başarı → `closed`, başarısızlık → tekrar `OPEN`.

Exponential backoff (gönderim başına) `retry.py`'de; bu breaker ise gönderimler-arası
sistemik hatayı kapsar. Tek uvicorn süreci için modül-singleton yeterli; çok-süreçli dağıtımda
paylaşımlı (Redis vb.) state gerekir (bkz. README "Yapamadıklarım").
"""

from __future__ import annotations

import threading
import time

from app.core.config import settings


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int, cooldown_seconds: float) -> None:
        self._failure_threshold = max(1, int(failure_threshold))
        self._cooldown = float(cooldown_seconds)
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Şu an gönderim denenebilir mi? OPEN + cooldown dolmadıysa ``False``."""
        with self._lock:
            if self._opened_at is None:
                return True
            return (time.monotonic() - self._opened_at) >= self._cooldown

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._failure_threshold:
                self._opened_at = time.monotonic()

    @property
    def is_open(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return False
            return (time.monotonic() - self._opened_at) < self._cooldown

    def reset(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None


_breaker: CircuitBreaker | None = None


def get_breaker() -> CircuitBreaker:
    """Süreç-genelinde tek breaker örneği (config eşikleriyle)."""
    global _breaker
    if _breaker is None:
        _breaker = CircuitBreaker(
            failure_threshold=settings.sync_circuit_failure_threshold,
            cooldown_seconds=settings.sync_circuit_cooldown_seconds,
        )
    return _breaker
