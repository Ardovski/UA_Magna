"""v1 validation router — validation.api'yi mount eder.

Veri kalite validasyonu (hatalı/şüpheli kayıt tespiti, raporu) endpoint'lerini
v1 yüzeyine bağlayan ince köprü. Asıl validasyon kuralları ve uygulaması
``app/features/validation`` altındadır; bu dosya yalnızca feature router'ını
mount eder.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.features.validation.api import router as validation_router

# v1 taşıyıcı router; tek görevi validation feature router'ını mount etmek.
router = APIRouter()
# Validation endpoint'lerini "validation" etiketi (Swagger grubu) altında dahil et.
router.include_router(validation_router, tags=["validation"])
