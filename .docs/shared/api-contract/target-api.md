# Hedef (Target) MES API Entegrasyonu — Bölüm 5.5 (Kritik %15)

> Sadece **valide + onaylı** kayıtlar gönderilir. Hatalı kaydın hedef sisteme ulaşmaması en
> kritik gereksinimlerden biridir. Tüm çağrılar **backend'de** (secret browser'a gitmez).
> Tam dokümantasyon: `http://89.252.189.91:8983/docs-guide`

## Endpoint
```
POST {TARGET_API_URL}/api/v1/submit
Header:  X-Production-Key: <key>          # .env'den
         Content-Type: application/json
```

## Gönderim Modeli — (gün, vardiya) bazında AGREGE
Case: "Gönderim her gün, 3 vardiya için ayrı ayrı." Payload kayıt-kayıt değil; her
`(production_date, shift)` için temiz kayıtlar **tek payload'a agrege** edilir:

| JSON alanı | Tip | Kaynak (agregasyon) | Kısıt |
|------------|-----|---------------------|-------|
| `production_date` | string | gün | `YYYY-MM-DD`, gelecek değil |
| `shift` | int | vardiya | 1 / 2 / 3 |
| `machine_count` | int | o vardiyada aktif distinct istasyon sayısı | 1–1000 |
| `total_production_units` | int | Σ Üretilen Miktar (**fire dahil** — kontrat: "including rejects") | 1–1.000.000 |
| `oe_value` | float | ort. OEE (üretimle ağırlıklı önerilir) | 0.0–100.0 |

### Örnek İstek
```http
POST /api/v1/submit
X-Production-Key: <your-key>
Content-Type: application/json

{ "machine_count": 12, "total_production_units": 4500,
  "oe_value": 87.3, "shift": 1, "production_date": "2025-11-05" }
```

### Başarılı Yanıt — **hedef MES API'sinden** (upstream `http://89.252.189.91:8983/api/v1/submit`)
> Bu yanıt **hedef MES API'sine** aittir; bizim yerel `/api/v1/sync/submit` endpoint'imiz **HTTP 202
> Accepted** + `SubmitResponse` döner (yukarıdaki sözleşme), bu `{success, submission_id, ...}` gövdesini değil.
```json
HTTP 200 OK
{ "success": true, "submission_id": 42, "candidate_name": "Umut Arda Özdeş",
  "message": "Data recorded successfully. ID #42.", "submitted_at": "2025-11-05T08:30:00" }
```
Hedefin `submission_id`'si → `sync_submissions.target_submission_id`'ye yazılır (idempotency kanıtı).

## Hata Kodları & Tepki
| Kod | Anlam | Tepkimiz |
|-----|-------|----------|
| 401 | Eksik/geçersiz API key | Dur, kullanıcıya "key kontrol" de (retry **etme**) |
| 422 | Validasyon hatası | `detail`'i logla+göster; payload'ı düzelt; retry etme |
| 429 | Rate limit | `TARGET_API_RATE_LIMIT_COOLDOWN_SECONDS` (60s) bekle, sonra retry |
| 413 | Body > 10KB | Batch'i böl (daha küçük gruplar) |
| 5xx | Sunucu hatası | Exponential backoff ile retry (max `TARGET_API_MAX_RETRIES`) |

## Idempotency (zorunlu)
- **Anahtar:** `idempotency_key = "{production_date}:{shift}"` (doğal anahtar) + `payload_hash`.
- Gönderim öncesi `sync_submissions`'a `pending` yazılır.
- Aynı `(gün, vardiya)` daha önce `success` ise **tekrar POST edilmez** (payload_hash aynıysa) → `skipped_already_success`.
- Veri değiştiyse (payload_hash farklı) → davranış `force` bayrağına bağlı: `force=false` ise grup `rejected_due_to_hash_conflict`'e düşer; `force=true` ise yeni bir `pending` gönderim oluşturulup `accepted`'a alınır.
- **Hedefleme önceliği:** `targets[]` (yalnız bu gruplar) > tek `(production_date, shift)` > hiçbiri verilmezse tüm geçerli gruplar.
- Sonuç: aynı kayıt 2 kez gönderilse de hedef sistemde duplicate oluşmaz.

## Retry / Backoff (el ile, `sync/retry.py`)
```
deneme = min(TARGET_API_MAX_RETRIES, n)              # max 3
5xx (500/502/503/504): bekleme = TARGET_API_BACKOFF_BASE_SECONDS ** deneme   # base=2 → 2,4,8...
429:                    sabit TARGET_API_RATE_LIMIT_COOLDOWN_SECONDS (60s) bekle (backoff DEĞİL)
network/timeout (TimeoutException, ConnectError, RemoteProtocolError): geçici sayılır, retry edilir
401/422/413 retry EDİLMEZ (kalıcı hata)
```
> Retry/backoff **el ile** `app/features/sync/retry.py` içinde yazılmıştır; `tenacity`
> `requirements`'ta tanımlı ama import edilip kullanılmaz.
>
> Not (gelecek/bonus, **henüz yok**): uzun süreli hata için circuit breaker. Mevcut kod yalnız
> gönderim başına `max_retries` + backoff/cooldown uygular; circuit breaker yoktur.

## Akış (sync feature)
```
1. preview   GET  /api/v1/sync/preview         gönderilecek (gün,vardiya) payload'ları göster
2. submit    POST /api/v1/sync/submit           HTTP 202 Accepted; gönderim arka planda (BackgroundTasks)
3. history   GET  /api/v1/sync/history          her gönderim: durum, http kodu, submission_id
4. retry     POST /api/v1/sync/{submission_id}/retry  başarısız gönderimi senkron yeniden dene
5. retry-all POST /api/v1/sync/retry-all        failed/retrying tümünü arka planda (202) yeniden dene
```

### `POST /api/v1/sync/submit` sözleşmesi
İstek (`SubmitRequest`):
```json
{ "production_date": "2025-11-05", "shift": 1,
  "targets": [{ "production_date": "2025-11-05", "shift": 2 }],
  "force": false }
```
Yanıt **HTTP 202 Accepted** (`SubmitResponse`); hedef API'ye gerçek HTTP teslimi bir background task içinde asenkron yapılır:
```json
{ "accepted": ["2025-11-05:1"],
  "skipped_already_success": ["2025-11-05:2"],
  "rejected_due_to_hash_conflict": [],
  "submission_ids": [42] }
```
`accepted` / `skipped_already_success` / `rejected_due_to_hash_conflict` → `idempotency_key` (`"{YYYY-MM-DD}:{shift}"`) listeleri (`list[str]`); `submission_ids` → `list[int]`.

## Güvenlik
- `X-Production-Key` **sadece** `.env` → backend. Log'a/response'a/frontend'e **asla**.
- `.env` gitignore'lu; `.env.example` placeholder ile paylaşılır.
- Mock geliştirme: gerçek endpoint erişilemezse `webhook.site`/`httpbin.org` ile geliştir,
  sonra `TARGET_API_URL`/`TARGET_API_KEY` değiştirip gerçek endpoint'e geç (case FAQ önerisi).
