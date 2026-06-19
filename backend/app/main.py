"""FastAPI giriş noktası.

Faz 0: app + logging + CORS + hata yönetimi + DB lifecycle + v1 router.
Feature router'ları `app/api/v1/router.py` üzerinden mount edilir.
Çalıştır: `make dev-api`  → http://localhost:8000/docs
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Dev kolaylığı: şema yoksa oluştur (create_all idempotent).
    init_db()
    logger.info("API başladı · env=%s", settings.app_env)
    yield


app = FastAPI(
    title="Üretim Performans Takip API",
    version="0.1.0",
    description="MAGNA case study — CSV import, validasyon, OEE analitik, hedef API sync.",
    lifespan=lifespan,
)

# CORS: yalnız .env'de izin verilen origin'ler (varsayılan: Next.js :3000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Domain hatalarını tutarlı JSON formatına çeviren handler'ları bağla.
register_error_handlers(app)
# Tüm feature endpoint'leri /api/v1 önekiyle yayınlanır.
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness — `make dev` sonrası doğrulama için."""
    return {"status": "ok", "env": settings.app_env}


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    """Kök endpoint — API kimliği ve Swagger doküman bağlantısını döndürür."""
    return {"name": "uretim-takip-api", "docs": "/docs", "version": "0.1.0"}
