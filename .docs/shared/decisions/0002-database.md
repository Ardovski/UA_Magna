# ADR 0002 — Veritabanı: SQLite + SQLAlchemy

**Durum:** Kabul edildi · **Tarih:** 2026-06-17

## Bağlam
SQLite case study'de **zorunlu**. Veri: ~2.117 satır (100K+ bonus hedefi). Düzeltme audit'i ve
idempotent sync log'u kalıcı tutulmalı. (Validasyon issue'ları kalıcı **tutulmaz**; yalnız türetilen
kayıt durumu `production_records.status`'a yazılır, issue'lar her istekte motorla canlı hesaplanır.)

## Karar
- SQLite, **SQLAlchemy ORM** ile. Runtime DB: `db/app.db` (repo kökü, gitignore'lu).
- 6 tablo: `import_batches`, `production_records`, `validation_issues`, `record_edits`,
  `sync_submissions`, `app_settings` (bkz. [`database.md`](../../api/database.md)).
  Not: `validation_issues` şemada tanımlı ama runtime'da hiç doldurulmaz (her zaman boş);
  issue'lar `run_validation` ile bellekte hesaplanır.
- Tekillik: `production_records.row_hash` unique; `sync_submissions.idempotency_key` unique.

## Alternatifler
| Alternatif | Neden hayır |
|------------|-------------|
| Ham `sqlite3` | ORM yok → şema/sorgu/migration el ile, daha hataya açık |
| Pandas-only (DB'siz) | Kalıcılık, audit trail, idempotency log gerekiyor |
| Postgres | Case SQLite zorunlu kılıyor; kurulum karmaşıklığı |

## Sonuçlar
- (+) Tek dosya DB → "3 komut kurulum"a uygun, taşınabilir.
- (+) ORM ile tip güvenli sorgu + index.
- (−) Eşzamanlı yazma sınırlı (SQLite) → tek kullanıcılı MVP için sorun değil.
- 100K+ satır (bonus): toplu insert (`bulk_insert_mappings`) + chunk'lı okuma planlandı.
