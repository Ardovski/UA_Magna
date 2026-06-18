# Veritabanı Şeması — SQLite

6 tablo: import takibi, üretim kayıtları, validasyon issue'ları (şema var, runtime'da boş), düzeltme audit trail'i, sync log, uygulama ayarları (key-value; aktif batch seçimi için `active_batch_id`).

## Tablolar

### `import_batches` — her CSV yükleme
| Alan | Tip | Not |
|------|-----|-----|
| id | int PK | |
| filename | text | yüklenen dosya adı |
| file_hash | text | SHA-256 — **aynı dosya tekrar yükleme tespiti** (5.1 duplicate) |
| uploaded_at | datetime | |
| total_rows | int | CSV'deki toplam satır |
| imported_rows | int | başarıyla içe alınan |
| rejected_rows | int | reddedilen |
| suspect_rows | int | şüpheli (uyarılı) |
| status | text | `processing` / `completed` / `failed` / `duplicate` (duplicate = `file_hash` daha önce import edilmiş; satırlar yine de import edilir, sadece batch durumu duplicate) |

### `production_records` — ana veri (18 kolon + meta)
| Alan | Tip | Not |
|------|-----|-----|
| id | int PK | iç PK |
| import_batch_id | int FK → import_batches | |
| record_id_src | int | CSV'deki `record_id` |
| prod_date | date | normalize edilmiş |
| work_order_no | text | |
| work_center_no / work_center_name | text | |
| station_name | text | |
| stock_name | text | |
| shift | int | 1/2/3 |
| availability, performance, quality, oee | float | kaynaktan |
| run_time, down_time, planned_down, unplanned_down | float | dakika |
| produced_qty, scrap_qty | int | |
| oee_recomputed | float | bizim hesabımız (çapraz kontrol) |
| row_hash | text | tekillik anahtarı hash'i (duplicate satır tespiti) |
| status | text | `valid` / `suspect` / `rejected` / `fixed` |
| created_at, updated_at | datetime | |

**Index:** `(prod_date, shift, station_name)`, `status`, `import_batch_id`.
**Unique:** `row_hash` (içerik-bazlı duplicate koruması).

### `validation_issues` — kayıt başına 0..N issue (şema var, runtime'da boş)

> **Not:** Bu tablo şemada tanımlı ancak **RUNTIME'DA HİÇ YAZILMAZ** (her zaman boş). Validasyon
> sonuçları engine'de canlı (`run_validation`) hesaplanır; tek kaynak doğruluk in-memory motor
> çıktısıdır (`validation/api.py:48-51`). `/issues` endpoint'i bu tablodan değil canlı motordan okur.
> Yalnız türetilen kayıt durumu `production_records.status`'a yazılır.

| Alan | Tip | Not |
|------|-----|-----|
| id | int PK | |
| record_id | int FK → production_records | |
| rule_id | text | örn. `V-C01` (kataloğa referans) |
| category | text | missing/range/consistency/duplicate/format/domain |
| severity | text | `error` / `warning` / `info` |
| field_names | text | etkilenen alan(lar) (JSON/CSV) |
| message | text | insan-okunur açıklama |
| suggested_action | text | `reject` / `warn` / `fix` |
| status | text | `open` / `fixed` / `rejected` / `accepted` |
| created_at | datetime | |

### `record_edits` — düzeltme audit trail (bonus, tercih edilen)
| Alan | Tip | Not |
|------|-----|-----|
| id | int PK | |
| record_id | int FK → production_records | |
| field | text | düzeltilen alan |
| old_value / new_value | text | |
| reason | text | düzeltme gerekçesi |
| edited_by | text | kullanıcı (MVP'de "operator") |
| edited_at | datetime | |

### `sync_submissions` — hedef API gönderim log'u (idempotency + retry)
| Alan | Tip | Not |
|------|-----|-----|
| id | int PK | |
| prod_date | date | gönderim (gün) |
| shift | int | gönderim (vardiya) |
| idempotency_key | text | **unique** (`uq_sync_idempotency_key`, String(40)) — `{prod_date}:{shift}` |
| payload_hash | text | agrege payload hash'i (içerik değişti mi) |
| status | text | `pending` / `success` / `failed` / `retrying` |
| http_status | int | hedef API yanıt kodu |
| target_submission_id | int | hedef sistemdeki `submission_id` |
| response_body | text | (secret'sız) yanıt |
| attempts | int | deneme sayısı |
| last_attempt_at | datetime | |
| created_at | datetime | |

**Unique:** `idempotency_key` → aynı (gün, vardiya) iki kez başarılı gönderilmez.

### `app_settings` — uygulama ayarları (key-value)
| Alan | Tip | Not |
|------|-----|-----|
| key | text PK | String(64) — örn. `active_batch_id` |
| value | text | ayar değeri |
| updated_at | datetime | |

## İlişkiler (özet)
```
import_batches 1───∞ production_records 1───∞ validation_issues  (şema var, runtime'da boş)
                                        1───∞ record_edits
sync_submissions  (prod_date, shift) ─ agrege ── production_records[status=valid]
app_settings  (key-value; active_batch_id)
```

## DBML (görselleştirme için)
```dbml
Table production_records {
  id int [pk]
  import_batch_id int [ref: > import_batches.id]
  record_id_src int
  prod_date date
  shift int
  oee float
  status text
  row_hash text [unique]
}
// validation_issues: şemada tanımlı ancak runtime'da hiç yazılmaz (her zaman boş)
Table validation_issues {
  id int [pk]
  record_id int [ref: > production_records.id]
  rule_id text
  severity text
  suggested_action text
}
Table sync_submissions {
  id int [pk]
  idempotency_key text [unique]
  prod_date date
  shift int
  status text
}
```
