"""v1 analytics router — analytics.api'yi mount eder.

Bu modül ince bir köprüdür: OEE/analitik endpoint'lerinin gerçek mantığı
``app/features/analytics/api`` içinde tanımlıdır. Buradaki router yalnızca o
feature router'ını v1 API yüzeyine bağlar. Endpoint eklemek/değiştirmek için
feature modülüne gidilmelidir, buraya değil.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.features.analytics.api import router as analytics_router

# v1 seviyesindeki taşıyıcı router; tek görevi feature router'ını mount etmek.
router = APIRouter()
# Analytics feature endpoint'lerini "analytics" etiketi altında dahil et
# (etiket Swagger/OpenAPI gruplaması için kullanılır).
router.include_router(analytics_router, tags=["analytics"])
