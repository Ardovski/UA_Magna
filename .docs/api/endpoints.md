# İç (Internal) API — FastAPI Endpoint'leri

Base: `http://localhost:8000` · Swagger: `/docs` · OpenAPI: `/openapi.json`
Feature yolları `/api/v1` altında. **İstisna:** `/health` ve `/` (root) app kökündedir,
`/api/v1` altında **değildir**.

## Health & Meta
| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/health` | liveness (app kökü, `/api/v1` değil) → `{status, env}` |
| GET | `/` | root (app kökü) |
| GET | `/api/v1/status` | meta → `{status:"ok", api:"v1"}` |

## Import (ingestion)
| Method | Path | Açıklama |
|--------|------|----------|
| POST | `/api/v1/imports/import` | multipart CSV yükle (UploadFile `file`) → parse + validate + import; `ImportSummary` döner |
| POST | `/api/v1/imports/preview` | yüklemeden önce ilk 10 satır önizleme (`ImportPreview` döner) |
| GET | `/api/v1/imports/batches` | yükleme geçmişi → `list[BatchOut]` |
| GET | `/api/v1/imports/batches/active` | aktif batch → `BatchOut \| null` |
| POST | `/api/v1/imports/batches/{batch_id}/activate` | batch'i aktif yap → `BatchOut` |
| DELETE | `/api/v1/imports/batches/{batch_id}` | batch sil (204) |

## Records (filtre / sorgu / export)
| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/api/v1/records/list` | filtreli + sayfalı liste. Query: `start,end,shift,station_name,stock_name,oee_min,oee_max,validation_status,has_issues,page,size,sort` → `PaginatedRecords {items,page,size,total,total_pages}` |
| GET | `/api/v1/records/export` | `/list` ile aynı filtre param'larıyla CSV indir (streaming UTF-8 BOM `text/csv`, `Content-Disposition: attachment`, `Cache-Control: no-store`) |
| GET | `/api/v1/records/distinct/{column}` | bir kolonun farklı değerleri (filtre seçenekleri) |
| GET | `/api/v1/records/{id}` | tek kayıt (dict); kayıt yoksa 404. (Issue'ları döndürmez.) |

## Validation
| Method | Path | Açıklama |
|--------|------|----------|
| POST | `/api/v1/validation/run` | validasyonu çalıştır (opsiyonel body `record_ids`); kayıt durumlarını yazar |
| GET | `/api/v1/validation/issues` | şüpheli/hatalı kayıtlar (filtreli). Query: `category, severity, rule_id, record_status` |
| GET | `/api/v1/validation/summary` | kategori/severity bazında dağılım + sistemik vs tekil |
| GET | `/api/v1/validation/report` | validasyon raporu |
| POST | `/api/v1/validation/records/{id}/fix` | manuel düzeltme (gövde: serbest patch dict) → `status='valid'`, `RecordEdit` (reason=`manual_fix`) yazar |
| POST | `/api/v1/validation/records/{id}/reject` | kaydı reddet (opsiyonel body `{reason}`; `status='rejected'`) |
| POST | `/api/v1/validation/records/{id}/accept` | şüpheliyi onayla (opsiyonel body `{reason}`; `status='valid'`) |
| GET | `/api/v1/validation/records/{id}/edits` | düzeltme geçmişi (`list[dict]`, `edited_at` azalan; kayıt yoksa 404) |

> **Issue'lar kalıcı değil:** `/issues` ve `/summary`/`/report`, `validation_issues` tablosundan
> değil; her istekte `run_validation` ile **bellekte canlı** hesaplanan motor çıktısından okur.
> `validation_issues` tablosu şemada tanımlı ama runtime'da hiç doldurulmaz.

## Analytics (dashboard)
| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/api/v1/analytics/kpis` | Ort. OEE, Toplam Üretim, Toplam Fire, Toplam Duruş (filtreli) |
| GET | `/api/v1/analytics/oee-trend` | günlük OEE serisi (`days` 1..90, varsayılan 21) |
| GET | `/api/v1/analytics/shift-comparison` | vardiya bazlı performans |
| GET | `/api/v1/analytics/station-ranking` | istasyon bazlı OEE sıralaması (`limit` 1..100, varsayılan 10) |
| GET | `/api/v1/analytics/quality-distribution` | fire/kalite dağılımı |
| GET | `/api/v1/analytics/recent-records` | son kayıtlar (`batch_id`, `limit`) |
| GET | `/api/v1/analytics/top-stations` | en iyi istasyonlar (`batch_id`, `limit`) |
| GET | `/api/v1/analytics/problem-shifts` | sorunlu vardiyalar (`batch_id`, `limit`) |
| GET | `/api/v1/analytics/filter-options` | filtre seçenekleri (param yok) → `{stations, stock_names, work_centers}` |

## Sync (hedef API)
| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/api/v1/sync/preview` | gönderilecek (gün,vardiya) agrege payload'ları |
| POST | `/api/v1/sync/submit` | **202 Accepted** döner; teslim `BackgroundTasks` ile arka planda yapılır. Body: `SubmitRequest {production_date?, shift?, targets?:[{production_date,shift}], force=false}`. Yanıt: `SubmitResponse {accepted:list[str idempotency_key], skipped_already_success, rejected_due_to_hash_conflict, submission_ids:list[int]}` |
| GET | `/api/v1/sync/history` | gönderim log'u: durum, http kodu, submission_id, deneme |
| POST | `/api/v1/sync/{id}/retry` | başarısız gönderimi yeniden dene; **senkron** olarak yeniden agrege edip gönderir. Kayıt yoksa 404; zaten `success` ise değiştirmeden döner |

## Ortak Yanıt Sözleşmesi
```json
// hata
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "detail": { } } }
// import özeti (ImportSummary)
{ "batch_id": 3, "filename": "rapor.csv", "file_hash": "…", "total_rows": 2117,
  "imported_rows": 1980, "duplicate_file": false, "duplicate_row_skipped": 12,
  "parse_failed_count": 5, "failed_rows_sample": [], "status": "completed", "elapsed_ms": 842,
  "validation": { "validated_records": 1980, "valid": 1843, "suspect": 102, "rejected": 35,
    "total_issues": 137, "by_severity": { "error": 35, "warning": 102, "info": 0 },
    "by_category": { "consistency": 60, "range": 25, "duplicate": 12 } } }
```

> Hedef (dış) API sözleşmesi ayrı: [`target-api.md`](../shared/api-contract/target-api.md).
