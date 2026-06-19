"""Ingestion feature — CSV → SQLite.

CSV'yi okur (utf-8/cp1254/latin-1 fallback), tarih/ondalık/yüzde ölçeğini
normalize eder, file_hash + row_hash üretir (duplicate tespiti), import_batch +
production_records'a yazar ve otomatik olarak validasyon motorunu çalıştırır.
Giriş noktaları: preview_csv, import_csv, list_batches, set_active_batch.
"""
