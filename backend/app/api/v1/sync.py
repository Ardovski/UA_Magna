"""v1 sync router — sync.api'yi mount eder.

Temiz/onaylı kayıtların harici hedef API'ye gönderimi (idempotent + retry)
endpoint'lerini v1 yüzeyine bağlayan ince köprü. Asıl gönderim mantığı
(idempotency key, retry/backoff) ``app/features/sync/api`` içindedir; burada
yalnızca mount yapılır.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.features.sync.api import router as sync_router

# v1 taşıyıcı router; tek görevi sync feature router'ını mount etmek.
router = APIRouter()
# Sync endpoint'lerini "sync" etiketi (Swagger grubu) altında dahil et.
router.include_router(sync_router, tags=["sync"])
