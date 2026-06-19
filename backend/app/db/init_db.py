"""DB şemasını oluştur (create_all) + basit additive migration. Çalıştır: `make db-init`.

SQLite dosyası repo kökündeki `db/app.db` (gitignore'lu). db/ dizini yoksa oluşturulur.

Schema versioning stratejisi: Alembic yerine pragmatik bir `ALTER TABLE ... ADD COLUMN`
döngüsü (idempotent) — mevcut kolonlar PRAGMA table_info ile kontrol edilir, yeni
eklenen kolonlar otomatik migrate edilir. Case study kapsamı (MVP, tek uvicorn worker)
için yeterli; çok-süreçli dağıtımda Alembic'e geçiş README'de not edildi.
"""
from __future__ import annotations

import logging

from sqlalchemy import Index, inspect, text

from app.core.config import DB_DIR
from app.db import models
from app.db.base import Base
from app.db.session import engine

_logger = logging.getLogger(__name__)

_EXTRA_INDEXES: tuple[Index, ...] = (
    Index("ix_record_oee", models.ProductionRecord.oee),
    Index("ix_record_stock_name", models.ProductionRecord.stock_name),
)

# Additive migration: (tablo, kolon_adı, kolon_tipi) — mevcut DB'de yoksa ALTER TABLE ile ekle.
# Yeni alanlar case §5.5 hedef API response'unu (candidate_name, message, submitted_at)
# yakalamak için eklendi; mevcut tablolar bu döngüyle migrate edilir.
_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    ("sync_submissions", "target_candidate_name", "VARCHAR(120)"),
    ("sync_submissions", "target_message", "TEXT"),
    ("sync_submissions", "target_submitted_at", "DATETIME"),
)


def _column_exists(table: str, column: str) -> bool:
    """PRAGMA table_info ile tablonun kolon listesini oku, kolon var mı kontrol et."""
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).all()
    return any(r[1] == column for r in rows)


def _run_migrations() -> list[str]:
    """Eksik kolonları idempotent biçimde ekler; eklenen kolon listesini döner (log/çıktı için)."""
    applied: list[str] = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table, column, col_type in _MIGRATIONS:
        if table not in existing_tables:
            # Tablo yoksa create_all sonrası zaten oluşacak; bekle.
            continue
        if _column_exists(table, column):
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        applied.append(f"{table}.{column}")
        _logger.info("migration.applied %s.%s (%s)", table, column, col_type)
    return applied


def init_db() -> None:
    """Tüm tabloları ve ek index'leri oluşturur (idempotent), sonra doğrular."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Modelde tanımlı olmayan ekstra index'ler (dashboard/filtre performansı için).
    for idx in _EXTRA_INDEXES:
        idx.create(bind=engine, checkfirst=True)
    # Additive migrations (yeni kolonlar) — create_all yeni tabloları kurar ama mevcut
    # tablolara ALTER yapmaz; burada yakalarız.
    applied = _run_migrations()
    if applied:
        print(f"  migrations applied: {applied}")
    # Doğrulama: beklenen tüm tablolar gerçekten oluşmuş mu? Eksikse erken hata ver.
    existing = set(inspect(engine).get_table_names())
    expected = set(Base.metadata.tables.keys())
    if not expected.issubset(existing):
        missing = expected - existing
        raise RuntimeError(f"DB init eksik tablolar: {sorted(missing)}")


if __name__ == "__main__":
    init_db()
    print(f"✓ DB şeması oluşturuldu ({DB_DIR / 'app.db'})")
