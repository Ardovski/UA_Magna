"""CLI seed — `python -m app.features.ingestion.seed <csv_path>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.features.ingestion.service import import_csv


def _print_summary(s) -> None:
    """Import özetini terminale okunaklı bir tablo olarak yazdırır."""
    print("=" * 64)
    print(f"  Batch #{s.batch_id}  {s.filename}")
    print(f"  file_hash      : {s.file_hash[:16]}...")
    print(f"  status         : {s.status}")
    print(f"  total_rows     : {s.total_rows}")
    print(f"  imported_rows  : {s.imported_rows}")
    print(f"  duplicate_file : {s.duplicate_file}")
    print(f"  dup_row_skipped: {s.duplicate_row_skipped}")
    print(f"  parse_failed   : {s.parse_failed_count}")
    print(f"  elapsed_ms     : {s.elapsed_ms}")
    print("=" * 64)


def main() -> int:
    """CLI giriş noktası: verilen CSV yolunu okur, import eder, özet yazdırır.

    Çıkış kodu: 0 başarılı, 1 import hatası, 2 dosya bulunamadı.
    """
    parser = argparse.ArgumentParser(description="CSV seed (ingestion).")
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    if not args.csv_path.exists():
        print(f"HATA: dosya bulunamadı → {args.csv_path}", file=sys.stderr)
        return 2
    data = args.csv_path.read_bytes()
    db = SessionLocal()
    try:
        summary = import_csv(db, data, args.csv_path.name)
        db.commit()  # CLI kendi session'ını yönetir; import_csv commit yapmaz
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"HATA: import başarısız → {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
