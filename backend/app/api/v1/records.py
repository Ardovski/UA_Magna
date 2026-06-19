"""v1 records router — records.api'yi mount eder.

Kayıt listeleme/filtreleme endpoint'lerini v1 yüzeyine bağlayan ince köprü.
Asıl sorgu/filtre mantığı ``app/features/records/api`` içindedir; bu dosyada
endpoint tanımı yoktur, yalnızca mount işlemi yapılır.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.features.records.api import router as records_router

# v1 taşıyıcı router; tek görevi records feature router'ını mount etmek.
router = APIRouter()
# Records endpoint'lerini "records" etiketi (Swagger grubu) altında dahil et.
router.include_router(records_router, tags=["records"])
