"""Ingestion tests — normalizer + service + seed."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from app.features.ingestion import normalizer
from app.features.ingestion.service import import_csv


def test_normalizer_date_four_formats() -> None:
    assert normalizer._detect_date("11.05.2025") == dt.date(2025, 5, 11)
    assert normalizer._detect_date("2025-11-05") == dt.date(2025, 11, 5)
    assert normalizer._detect_date("11/05/2025") == dt.date(2025, 11, 5)
    assert normalizer._detect_date("05/11/2025") == dt.date(2025, 5, 11)
    assert normalizer._detect_date(None) is None
    assert normalizer._detect_date("") is None


def test_normalizer_decimal_comma_and_dot() -> None:
    assert normalizer._to_float("87,3") == 87.3
    assert normalizer._to_float("87.3") == 87.3
    assert normalizer._to_float("0,5") == 0.5
    assert normalizer._to_float("abc") is None


def test_normalizer_percent_scale_in_unit() -> None:
    rescaled = normalizer._rescale_to_percent([0.87, 0.5, 0.99])
    assert rescaled == [87.0, 50.0, 99.0]
    mixed = normalizer._rescale_to_percent([0.5, 80.0, 95.0])
    assert mixed == [0.5, 80.0, 95.0]


def test_normalizer_string_trim_lower() -> None:
    assert normalizer._normalize_str("  IMM-2700-3  ") == "imm-2700-3"
    assert normalizer._normalize_str(None) is None
    assert normalizer._normalize_str("") is None


def test_normalizer_column_map() -> None:
    mapped = normalizer.map_columns(["record_id", "Tarih", "Vardiya", "OEE"])
    assert mapped == ["record_id_src", "prod_date", "shift", "oee"]


def test_service_import_success(db, sample_csv_bytes: bytes) -> None:
    summary = import_csv(db, sample_csv_bytes, "sample.csv")
    assert summary.total_rows == 5
    assert summary.imported_rows == 5
    assert summary.parse_failed_count == 0
    assert summary.duplicate_file is False
    assert summary.status == "completed"
    db.commit()


def test_service_duplicate_file_flag(db, sample_csv_bytes: bytes) -> None:
    s1 = import_csv(db, sample_csv_bytes, "sample.csv")
    db.commit()
    s2 = import_csv(db, sample_csv_bytes, "sample.csv")
    db.commit()
    assert s1.status == "completed"
    assert s2.status == "duplicate"
    assert s2.duplicate_file is True
    assert s2.imported_rows == 0


def test_service_parse_failed(db) -> None:
    bad = b"record_id,Tarih,Is Emri No\n\n"
    summary = import_csv(db, bad, "bad.csv")
    assert summary.total_rows == 0
    assert summary.parse_failed_count == 0
    db.commit()


def test_service_normalize_handles_missing_required(db) -> None:
    rows = (
        b"record_id,Tarih,Is Emri No,Is Merkezi No,Ismerkezi Adi,Is Istasyon Adi,Stok Adi,Vardiya,"
        b"A (Kullanilirlik),P (Performans),Q (Kalite),OEE,Calisma Suresi,Durus Suresi,"
        b"Planli Durus Suresi,Plansiz Durus Suresi,Uretilen Miktar,Hatali Uretilen Miktar\n"
        b"1,2025-11-05,3021234567,INJ,INJ,IMM-2700-3,STK-1,1,90,90,90,72.9,5.0,0.5,0.3,0.2,10,0\n"
    )
    summary = import_csv(db, rows, "ok.csv")
    assert summary.parse_failed_count == 0
    assert summary.imported_rows == 1
    db.commit()


def test_service_row_hash_skip_on_duplicate(db) -> None:
    rows = (
        b"record_id,Tarih,Is Emri No,Is Merkezi No,Ismerkezi Adi,Is Istasyon Adi,Stok Adi,Vardiya,"
        b"A (Kullanilirlik),P (Performans),Q (Kalite),OEE,Calisma Suresi,Durus Suresi,"
        b"Planli Durus Suresi,Plansiz Durus Suresi,Uretilen Miktar,Hatali Uretilen Miktar\n"
        b"1,11.05.2025,3027854094,INJ,INJ,IMM-2700-3,STK-1,1,0,0,0,0,2.05,2.05,0,2.05,0,0\n"
    )
    s1 = import_csv(db, rows, "a.csv")
    db.commit()
    s2 = import_csv(db, rows, "b.csv")
    db.commit()
    assert s1.imported_rows == 1
    assert s2.imported_rows == 0
    assert s2.duplicate_row_skipped == 1


def test_seed_production_data_csv(db) -> None:
    # backend/tests/test_ingestion.py → parents[2] = repo kökü
    csv_path = Path(__file__).resolve().parents[2] / "data" / "production_data.csv"
    if not csv_path.exists():
        pytest.skip(f"production_data.csv bulunamadı: {csv_path}")
    data = csv_path.read_bytes()
    summary = import_csv(db, data, csv_path.name)
    db.commit()
    assert summary.total_rows > 2000
    assert summary.imported_rows == summary.total_rows
    assert summary.duplicate_file is False
    assert summary.parse_failed_count == 0
    assert summary.elapsed_ms >= 0
