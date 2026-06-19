"""v1 imports router — ingestion.api'yi mount eder.

CSV import (MES raporu → SQLite) endpoint'lerini v1 yüzeyine bağlayan ince
köprü. Asıl import/ingestion mantığı ``app/features/ingestion/api`` içindedir;
endpoint davranışı (ör. yükleme, arka plan işleme) orada tanımlanır.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.features.ingestion.api import router as ingestion_router

# v1 taşıyıcı router; tek görevi ingestion feature router'ını mount etmek.
router = APIRouter()
# Ingestion endpoint'lerini "imports" etiketi (Swagger grubu) altında dahil et.
router.include_router(ingestion_router, tags=["imports"])
