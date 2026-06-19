"""FastAPI giriş noktası.

Faz 0: app + logging + CORS + hata yönetimi + DB lifecycle + v1 router.
Feature router'ları `app/api/v1/router.py` üzerinden mount edilir.
Çalıştır: `make dev-api`  → http://localhost:8000/docs
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db

setup_logging()
logger = get_logger(__name__)

# Otomatik seed için bakılacak CSV: repo kökü / data / production_data.csv.
# AUTO_SEED=1 (varsayılan .env.example'ta) + dosya mevcut + DB'de batch yok →
# ilk açılışta `data/production_data.csv` import edilir (file_hash + row_hash
# dedupe sayesinde idempotent; restart'larda no-op). Bu, `make dev` veya
# bare `uvicorn main:app --reload` ile başlayan kullanıcıya "sıfır-data"
# boş ekran göstermemek içindir (case §7.2 "veri gelmezse dashboard boş"
# senaryosunu önler). Devre dışı bırakmak için: AUTO_SEED=0.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_CSV = _REPO_ROOT / "data" / "production_data.csv"


def _auto_seed_if_needed() -> None:
    """AUTO_SEED=1 + CSV mevcut + DB boşken `production_data.csv` import et.

    import_csv kendi başına file_hash ile aynı dosyayı tekrar import etmez;
    row_hash dedupe ile aynı satırlar eklenmez. Bu yüzden restart güvenli.
    Hata olursa logla, uygulamayı durdurma — kullanıcı elle seed atabilir.
    """
    if not settings.auto_seed:
        logger.info("seed.disabled AUTO_SEED=0")
        return
    if not _SEED_CSV.exists():
        logger.warning("seed.skipped csv_missing=%s", _SEED_CSV)
        return
    from sqlalchemy import select

    from app.db import models
    from app.db.session import SessionLocal
    from app.features.ingestion.service import import_csv

    db = SessionLocal()
    try:
        existing = db.execute(select(models.ImportBatch.id).limit(1)).first()
        if existing is not None:
            logger.info("seed.skipped db_not_empty (manual seed gerekli değil)")
            return
        data = _SEED_CSV.read_bytes()
        summary = import_csv(db, data, _SEED_CSV.name)
        db.commit()
        logger.info(
            "seed.ok file=%s imported=%s duplicate_file=%s elapsed_ms=%s",
            summary.filename,
            summary.imported_rows,
            summary.duplicate_file,
            summary.elapsed_ms,
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning(
            "seed.failed err=%s (manuel: python -m app.features.ingestion.seed %s)",
            exc,
            _SEED_CSV,
        )
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Dev kolaylığı: şema yoksa oluştur (create_all idempotent).
    init_db()
    # İlk açılışta CSV'yi otomatik import et (kullanıcı sıfır-data görmesin).
    _auto_seed_if_needed()
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
