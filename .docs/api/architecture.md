# Mimari — Backend (FastAPI)

## Katmanlar

```
app/
├── main.py            # FastAPI() oluştur, CORS, router mount, exception handler
├── core/
│   ├── config.py      # Settings (pydantic-settings) — .env'den okur
│   ├── logging.py     # yapılandırılmış log
│   └── errors.py      # özel exception'lar + handler'lar (tutarlı JSON hata)
├── db/
│   ├── session.py     # SQLAlchemy engine + SessionLocal + get_db()
│   ├── models.py      # ORM modelleri (tablolar)
│   └── init_db.py     # create_all (make db-init)
├── schemas/           # Pydantic I/O modelleri (request/response DTO)
└── features/
    ├── ingestion/     # service.py (parse/normalize/import), seed.py
    ├── validation/    # engine.py + rules/ (kural başına dosya) + report.py
    ├── analytics/     # service.py (OEE recompute, KPI, trend agregasyonları)
    ├── records/       # service.py (filtre/sorgu), export.py (CSV)
    └── sync/          # client.py (httpx), service.py (agrege+idempotency+retry)
└── api/v1/            # router'lar: imports, records, validation, analytics, sync (+ /status meta). GET /health app kökünde
```

## İstek Akışı (örnek: CSV import)
```
POST /api/v1/imports/import (multipart)   # ayrıca POST /api/v1/imports/preview
   api/v1/imports.py (yalnız features/ingestion/api.py'yi re-mount eder)
     features/ingestion/service.py: parse + normalize + duplicate-check
       features/validation/engine.py: her satıra kuralları uygula
         db/models.py: yalnız production_records.status yazılır
                       (validation_issues tablosuna yazılmaz — issue'lar her istekte
                        run_validation ile bellekte hesaplanır)
       schemas: ImportSummary döndür
```

## Feature Modülü Anatomisi (konvansiyon)
Her feature kendi içinde:
- `router` → HTTP (api/v1 altında)
- `service.py` → iş mantığı (saf, test edilebilir)
- `schemas` (paylaşılan `app/schemas/` veya feature-içi)
- `tests/unit/test_<feature>.py`

İş mantığı router'da **değil** service'te. Router yalnız: doğrula (Pydantic) → service çağır → yanıtla.

## Konfigürasyon (core/config.py)
`pydantic-settings.BaseSettings` ile `.env` okunur:
`TARGET_API_URL`, `TARGET_API_KEY`, `DATABASE_URL`, `CORS_ALLOW_ORIGINS`, retry/timeout ayarları.
Secret asla log'lanmaz, asla response'a konmaz.

## Hata Yönetimi
- Domain hataları → özel exception (`ValidationError`, `DuplicateImportError`, `TargetApiError`).
- `core/errors.py` global handler → tutarlı JSON: `{ "error": { "code", "message", "detail" } }`.
- Hedef API hataları (401/422/429/413) tipli olarak yakalanır (bkz. sync).

## OpenAPI / Swagger (bonus — bedava gelir)
FastAPI otomatik `/docs` (Swagger) + `/openapi.json` üretir → değerlendirme "API tasarımı" +
bonus "OpenAPI/Swagger" maddesini karşılar.

## İç API Endpoint'leri
 [`endpoints.md`](endpoints.md)
