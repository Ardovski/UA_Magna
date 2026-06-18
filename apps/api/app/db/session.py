"""Veritabanı engine + session yönetimi (SQLite)."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite + FastAPI: aynı bağlantının farklı thread'lerde kullanımı için gerekli.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Iterator[Session]:
    """FastAPI dependency — istek başına session açar.

    Başarılı istekte commit, hata durumunda rollback eder. Aksi halde
    `autocommit=False` ile session kapanışında transaction rollback olur ve
    yazmalar (import, manuel düzelt/reddet/onayla) kalıcı olmaz.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
