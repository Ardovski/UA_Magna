"""Pytest configuration — fresh isolated SQLite per test session."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

os.environ["TARGET_API_KEY"] = "test-key-redacted"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["APP_ENV"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"

import contextlib

import pytest
from app.db import models  # noqa: F401  — Base.metadata'ya kayıt
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_engine():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    eng = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()
    with contextlib.suppress(FileNotFoundError):
        os.unlink(path)


@pytest.fixture
def TestSessionLocal(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture
def db(test_engine, TestSessionLocal) -> Iterator:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def _clean_tables(test_engine, TestSessionLocal):
    yield
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client(test_engine, TestSessionLocal):
    from app.db import session as session_module
    from app.main import app
    from fastapi.testclient import TestClient

    session_module.engine = test_engine
    session_module.SessionLocal = TestSessionLocal
    return TestClient(app)


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return (
        b"record_id,Tarih,Is Emri No,Is Merkezi No,Ismerkezi Adi,Is Istasyon Adi,Stok Adi,Vardiya,"
        b"A (Kullanilirlik),P (Performans),Q (Kalite),OEE,Calisma Suresi,Durus Suresi,"
        b"Planli Durus Suresi,Plansiz Durus Suresi,Uretilen Miktar,Hatali Uretilen Miktar\n"
        b"1,11/5/2025,3027854094,INJ,INJ,IMM-2700-3,STK-1,1,0,0,0,0,2.05,2.05,0,2.05,0,0\n"
        b"2,11/5/2025,3029724496,INJ,INJ,IMM-2700-3,STK-2,2,100,141.87,100,141.87,3.38,0,0,0,3,0\n"
        b"3,11.05.2025,3021111111,INJ,INJ,IMM-2700-3,STK-3,3,87,3,90,23.49,5.0,1.0,0.5,0.5,10,1\n"
        b"4,2025-11-06,3022222222,INJ,INJ,IMM-2700-3,STK-4,1,95,98,99,92.06,7.0,0.5,0.3,0.2,15,0\n"
        b"5,11/07/2025,3023333333,INJ,INJ,IMM-2700-4,STK-5,2,80,90,100,72.0,4.0,0.0,0.0,0.0,8,0\n"
    )
