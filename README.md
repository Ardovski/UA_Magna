# Üretim Performans Takip Uygulaması

> MAGNA — Mühendislik Aday Değerlendirme Case Study · **Aday: Umut Arda Özdeş**
> Otomotiv yan sanayi (enjeksiyon kalıplama) hattı için OEE & üretim kalite takip uygulaması.

[![Durum](https://img.shields.io/badge/durum-aktif-success)]() &nbsp;
[![Tests](https://img.shields.io/badge/pytest-38%20passing-success)]() &nbsp;
[![Rules](https://img.shields.io/badge/validasyon-43%20kural%20%2F%206%20kategori-blue)]()

Stack: **Next.js 14 + shadcn/ui** · **FastAPI + Pydantic v2** · **SQLite + SQLAlchemy 2.0** &nbsp; · &nbsp;
[API Swagger](http://localhost:8000/docs) &nbsp; · &nbsp;
[Tam kural kataloğu](.docs/shared/domain/validation-rules.md)

---

## 📌 Projenin Amacı

MES sisteminden gelen `.csv` üretim raporlarını içe aktaran, **veri kalitesini doğrulayan**,
OEE / üretim / fire / duruş metriklerini raporlayan ve **yalnızca doğrulanmış veriyi** merkezi
sisteme REST API ile gönderen tam-stack web uygulaması. Excel'de manuel, hataya açık ve yavaş olan
süreci uçtan uca otomatikleştirir.

Gerçek MES verisi "temiz" değildir: eksik alanlar, aralık dışı yüzdeler, mantıksal tutarsızlıklar
(ör. fire > üretim), duplicate'ler ve format kaymaları içerir. Bu uygulamanın merkezi değeri bu
sorunları **yakalamak, sınıflandırmak, gerekçelendirmek** ve hatalı kaydın merkezi API'ye
ulaşmasını engellemektir.

**4 aşamalı pipeline:**

1. **Import** — CSV → pandas normalize → SQLite (`import_batches` + `production_records`).
2. **Validate** — iki geçişli (row + batch) kural motoru; her kayda `valid / suspect / rejected` statüsü atar.
3. **Dashboard / Filter** — OEE trendi, vardiya/istasyon kırılımı, kalite dağılımı; çok kriterli filtre + CSV export.
4. **Sync** — **yalnızca `status='valid'`** kayıtlar, (gün, vardiya) bazında agrege edilip idempotent + retry'lı şekilde hedef API'ye gönderilir.

**Kapsam:** `data/production_data.csv` — **2.117 satır · 18 kolon · 21 gün** (5–25 Kasım 2025)
gerçekçi MES verisi.

## 🔄 Nasıl Çalışır (Uçtan Uca Akış)

### Ağ topolojisi

```
Browser (Next.js, :3000)
   │  fetch('/api/v1/...')  ── same-origin proxy (CORS gerekmez)
   ▼
Next.js rewrites()  (next.config.mjs)
   │  /api/v1/:path*  →  BACKEND_INTERNAL_URL (default http://localhost:8000)
   ▼
FastAPI (:8000)  ── tüm iş mantığı + DB
   │  POST {TARGET_API_URL}/api/v1/submit   header: X-Production-Key
   ▼
Hedef API (http://89.252.189.91:8983)
```

> **Secret yalnızca backend'de.** `X-Production-Key` `.env` → FastAPI'de okunur; tarayıcıya,
> log'a veya response'a asla sızmaz (log'da `***REDACTED***`). Frontend `NEXT_PUBLIC_API_URL`
> varsayılanı boş string'tir → tarayıcı relative `/api/v1/...` çağırır, Next.js proxy'ler.
> Doğrudan cross-origin erişim (örn. `NEXT_PUBLIC_API_URL=http://localhost:8000`) için backend
> `CORSMiddleware` + `CORS_ALLOW_ORIGINS` allow-list'i de sağlar (varsayılan `http://localhost:3000`).

### Veri akışı (adım adım)

**1) Import (`app/features/ingestion`).**
`POST /api/v1/imports/import` çok-parçalı CSV'yi alır. `_read_dataframe` sırayla `utf-8`, `cp1254`,
`latin-1` encoding dener. Kolonlar İngilizce identifier'lara map'lenir, satırlar normalize edilir
(tarih → ISO, ondalık virgül → nokta, yüzde 0–1 ölçeği → 0–100, string trim/case). `file_hash`
hesaplanır. Bir `ImportBatch` (`status='processing'`) oluşturulur; her satır için `row_hash`
hesaplanır, DB'de zaten var olan `row_hash`'ler atlanır (`duplicate_row_skipped`). Kalan satırlar
`ProductionRecord` olarak eklenir ve `oee_recomputed` alanı `recompute_oee` ile hesaplanır.

- **Duplicate dosya:** yeni `file_hash` mevcut bir batch ile eşleşirse batch `status='duplicate'`
  + açıklama mesajı alır — **ama satırlar yine de import edilir** (row_hash dedupe'a tabi).
- **Aktif batch:** import **otomatik aktif yapmaz**; aktif batch `app_settings.active_batch_id`'de
  tutulur ve yalnızca `POST /imports/batches/{id}/activate` ile değişir.
- `POST /api/v1/imports/preview` aynı normalize'i çalıştırır ama **DB'ye yazmaz** (ilk 10 satır örnek).

**2) Otomatik validasyon (import sonrası).**
Import biter bitmez `import_csv`, yeni kayıt id'leri üzerinde `run_validation` çağırır. Batch'in
`imported_rows / suspect_rows / rejected_rows` sayaçları bu özetten doldurulur.

**3) İki geçişli validasyon motoru (`app/features/validation`).**

- **PASS 1 (row pass):** her `ProductionRecord` için bir proxy kurulur ve `ALL_RULES` (41 satır
  kuralı) kayıt başına çalışır.
- **PASS 2 (batch pass):** tüm satırlar tarandıktan sonra iki batch-only kural çalışır (toplam
  41 + 2 = **43 kural**):
  - **V-D02** (iş anahtarı çakışması): kayıtlar `(prod_date, shift, station_name, work_order_no)`
    ile gruplanır; aynı kovada `(produced_qty, scrap_qty, oee)` metrikleri farklı olan ≥2 id varsa
    hepsi çelişkili işaretlenir.
  - **V-X05** (üretim outlier): z-score (popülasyon std, ≥5 değer, `|z| > 3.0`) ile aykırı
    `produced_qty` değerleri WARNING olarak işaretlenir.
- **Statü türetimi (yalnızca severity'den):** kayıtta herhangi bir **ERROR** → `rejected`;
  yoksa herhangi **WARNING** → `suspect`; aksi halde `valid`. (INFO tek başına statü değiştirmez.)
  Türetilen statü `production_records.status` kolonuna yazılır.

> **Önemli — Issue'lar kalıcı değildir.** `validation_issues` tablosu şemada tanımlıdır fakat
> **hiçbir zaman yazılmaz**. Tek doğruluk kaynağı canlı motor çıktısıdır: `/validation/issues`,
> `/summary`, `/report`, `/run` her çağrıda `run_validation`'ı yeniden çalıştırır. Yalnızca
> türetilmiş `status` (production_records'ta) ve manuel düzeltme audit'i (`record_edits`) kalıcıdır.

**4) Manuel düzeltme.**
Operatör bir kaydı düzeltebilir (`/fix` → `status='valid'`), reddedebilir (`/reject` →
`status='rejected'`) veya kabul edebilir (`/accept` → `status='valid'`). Her işlem
`record_edits` tablosuna audit satırı yazar (`edited_by='operator'`). Bu manuel override'lar
severity'den türetilen statüyü ezer.

**5) Dashboard & filtre (`app/features/analytics`, `records`).**
KPI'lar, OEE trendi, vardiya karşılaştırması, istasyon sıralaması, kalite dağılımı ve "son
kayıtlar / top istasyonlar / sorunlu vardiyalar" tabloları sunulur. `records/list` sunucu-taraflı
sayfalama + sıralama + zengin filtreyle (tarih, vardiya, istasyon, stok, OEE min/max, statü,
"sorunlu") çalışır; `records/export` UTF-8 BOM'lu CSV stream'i indirir.

**6) Sync (`app/features/sync`).**
Yalnızca `status='valid'` kayıtlar (gün, vardiya) bazında agrege edilir. Her grup için:

- `idempotency_key = "{YYYY-MM-DD}:{shift}"` (ör. `2025-11-05:1`), DB'de unique.
- `payload_hash = sha256(canonical JSON)` — payload `{production_date, shift, machine_count,
  total_production_units, oe_value (4 ondalık)}`.

`POST /sync/submit` **202 Accepted** döner ve gerçek HTTP teslimatı `BackgroundTasks` ile **arka
planda** yapılır. Hedef API'ye `httpx` ile POST edilir; retry/backoff matrisi uygulanır (aşağıda).

## 🏗 Mimari & Yöntemler

| Konu | Yaklaşım |
|------|----------|
| **Feature izolasyonu** | `eslint-plugin-boundaries`: `app → app/feature/shared`, `feature → yalnız shared + aynı feature`, `shared → shared`. Cross-feature import ve `@/features/*/*` deep import **lint hatası**. |
| **State ayrımı** | Server-state = **TanStack Query** (cache, `refetchInterval` ile sync geçmişi 3s'de bir canlı); UI-state = **Zustand** (`src/stores/filters.ts`, URL serileştirme ile paylaşılabilir filtre). |
| **Token-tabanlı tema** | Yalnızca Tailwind semantic token'ları (`bg-card`, `text-oee-good`…). Hardcoded renk yasak → dark mode bedava. |
| **İki geçişli validasyon** | Row-pass (kayıt başına saf kurallar) + batch-pass (gruplama gerektiren V-D02 / V-X05). |
| **Idempotency** | `idempotency_key` (unique) + `payload_hash` (SHA-256 canonical JSON). Aynı key + aynı hash → skip; farklı hash → `force` gerekir. |
| **Retry matrisi** | Yalnız **429** (60s cooldown) + **5xx** (500/502/503/504) ve ağ/timeout istisnaları retry edilir; **401 / 422 / 413 kalıcı hata**. Exponential backoff (`base ** attempt`, base=2), max 3 deneme. |
| **Background tasks** | `/submit` anında 202 döner; gerçek gönderim arka planda kendi `SessionLocal`'ında `execute_pending` ile çalışır. |
| **Re-agregasyon** | `execute_pending` / `retry_submission` göndermeden önce grubu yeniden agrege eder; valid kayıt kalmadıysa submission `failed ('no valid records to aggregate')` olur. |

> Detaylı karar belgeleri: [`.docs/shared/decisions/`](.docs/shared/decisions/).

## 🗂 Proje Yapısı

```
.
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── main.py                # uygulama girişi; /health, /, v1 router (prefix /api/v1)
│   │   ├── api/v1/                # router birleştirme (imports/records/validation/analytics/sync)
│   │   ├── core/                  # config.py (Settings/env), oee.py (recompute_oee)
│   │   ├── db/                    # models.py (6 tablo), init_db.py
│   │   └── features/
│   │       ├── ingestion/         # CSV oku/normalize/import, batch yönetimi, seed
│   │       ├── validation/        # engine.py (2-pass) + rules/ (43 kural, 6 kategori) + report.py
│   │       ├── records/           # liste/filtre/sayfalama/export/distinct
│   │       ├── analytics/         # KPI, OEE trend, vardiya/istasyon, kalite dağılımı
│   │       └── sync/              # aggregator, client (httpx), retry matrisi, service, api
│   ├── main.py                    # Case §7.2 shim: `from app.main import app`
│   ├── tests/                     # conftest + oee/ingestion/sync/validation (38 test)
│   └── requirements.txt
├── frontend/                      # Next.js 14 (App Router) + TypeScript
│   └── src/
│       ├── app/                   # route'lar
│       ├── components/ lib/ hooks/ stores/ types/   # shared katman (env.ts, api/client.ts, filters.ts)
│       └── features/
│           ├── import/            # ImportDropzone (drag&drop + multiple), ImportProgress, mergeSummaries
│           ├── dashboard/         # KPI grid + 4 recharts grafik + 3 tablo (Tabs)
│           ├── records/           # FilterPanel, RecordsTable (TanStack), ExportButton
│           ├── validation/        # ValidationPage, IssueList, IssueDetailDrawer, FixRejectButtons
│           └── sync/              # SyncPage (multi-select targets), HistoryTable (per-row retry)
├── db/                            # SQLite veritabanı evi (app.db + README.md)
├── data/                          # production_data.csv (2.117 satır, commit edilir)
├── .docs/                         # mimari + domain + api-contract + decisions dokümanları
├── .roadmap/                      # roadmap.md + CHECKLIST.md
├── ai_usage/                      # AI prompt/transcript/screenshot logları (case §8)
├── scripts/                       # new-ai-prompt.sh, backup-sessions.sh
├── Makefile · README.md · .env.example · AGENTS.md + CLAUDE.md
```

## 🧰 Teknoloji Yığını

### Backend

| Kütüphane | Sürüm | Neden |
|-----------|-------|-------|
| FastAPI | `>=0.110` | Pydantic ile birinci sınıf validasyon + otomatik OpenAPI/Swagger |
| Uvicorn | `>=0.29` | ASGI sunucu (`--reload` dev) |
| Pydantic / pydantic-settings | `>=2.6` / `>=2.2` | I/O doğrulama + `.env` secret yönetimi |
| python-multipart | `>=0.0.9` | Çok-parçalı CSV upload |
| pandas | `>=2.2` | CSV parse, normalize (tarih/ondalık/yüzde), groupby agregasyon |
| SQLAlchemy | `>=2.0` | `Mapped[]` tip-güvenli ORM (6 tablo) |
| httpx | `>=0.27` | Hedef API senkron HTTP client (timeout, redaction) |
| tenacity | `>=8.2` | requirements'ta bildirilen retry kütüphanesi — **fiili retry/backoff elle `sync/retry.py`'de** uygulandı (tenacity şu an import edilmiyor) |
| python-dotenv | `>=1.0` | `.env` yükleme |
| openpyxl | `>=3.1` | (rapor export için hazır bağımlılık) |

### Frontend

| Kütüphane | Sürüm | Neden |
|-----------|-------|-------|
| Next.js | `14.2.15` | App Router; `rewrites()` ile same-origin API proxy; `output: 'standalone'` |
| React / React-DOM | `18.3.1` | UI |
| @tanstack/react-query | `^5.51.0` | Server-state cache + canlı refetch |
| @tanstack/react-table | `^8.20.0` | Records/issue tabloları (sunucu sayfalama, sıralama) |
| zustand | `^4.5.5` | UI/filtre state |
| recharts | `^2.12.7` | OEE trend / vardiya / istasyon / kalite grafikleri |
| tailwindcss | `^3.4.10` | Token-tabanlı stil |
| zod / react-hook-form | `^3.23.8` / `^7.53.0` | Form + şema doğrulama |
| date-fns / lucide-react / sonner | `^3.6.0` / `^0.441.0` / `^1.5.0` | Tarih, ikon, toast |
| next-themes | `^0.3.0` | Dark mode |
| eslint-plugin-boundaries | `^4.2.2` | Feature izolasyonu (mimari lint) |
| TypeScript / ESLint | `5.9.3` / `^8.57.0` | Tip güvenliği + lint (`no-explicit-any` error) |

## ⚙ Hızlı Kurulum (3 komuttan az)

```bash
git clone https://github.com/<kullanici>/umut-arda-ozdes-uretim-takip-case.git
cd umut-arda-ozdes-uretim-takip-case
make setup            # .env kopyalar + backend venv + frontend npm kurar
```

> Ardından `.env` içindeki `TARGET_API_KEY`'i case'ten gelen gerçek key ile doldurun
> (varsayılan boştur; `.env.example`'da `buraya-production-key-gelecek` placeholder'ı vardır).
> `data/production_data.csv` repoda hazırdır (case'in runtime verisi).

## ▶ Çalıştırma

```bash
make dev              # web → http://localhost:3000   ·   api → http://localhost:8000/docs
```

| Komut | İş |
|-------|----|
| `make dev` | api (:8000) + web (:3000) birlikte |
| `make dev-api` / `make dev-web` | tek servis |
| `make db-init` | SQLite şema (`python -m app.db.init_db`) |
| `make seed` | `data/production_data.csv` import (`python -m app.features.ingestion.seed`) |
| `make db-reset` / `make clean-db` | DB sıfırla / temizle |
| `make test` / `make test-api` / `make test-web` | testler |
| `make lint` / `make format` / `make typecheck` | kalite araçları |
| `make check` | lint + typecheck + test (CI eşdeğeri) |
| `make ai-sync` | `AGENTS.md` → `CLAUDE.md` senkron |
| `make ai-backup` / `make ai-prompt name=<konu>` | AI transcript/prompt logları → `ai_usage/` |
| `make doctor` / `make help` | ortam kontrolü / tüm komutlar |

### Case §7.2 — birebir komutlar (Makefile'sız)

`backend/main.py`, `app.main:app`'i yeniden export eden ince bir shim'dir (case'in
`uvicorn main:app` komutu çalışsın diye). `db/` ise SQLite veritabanının evidir
(`db/app.db` + [`db/README.md`](db/README.md)). Şu komutlar Makefile olmadan da çalışır:

```bash
cp .env.example .env

# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload            # → http://localhost:8000/docs

# Frontend (ayrı terminal)
cd frontend && npm install && npm run dev
```

> **Port notu:** Frontend Next.js olduğu için dev sunucusu `http://localhost:3000`'de açılır
> (Vite varsayılanı 5173 değil). Tek komutla her ikisi için önerilen yol `make dev`'dir.

**Portlar:**

| Servis | URL |
|--------|-----|
| Web (Next.js) | http://localhost:3000 |
| API (FastAPI) | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| API health | http://localhost:8000/health |
| API v1 meta | http://localhost:8000/api/v1/status |

## 🔧 Ortam Değişkenleri (`.env`)

`make setup` `.env.example`'ı `.env`'e kopyalar. Secret yalnız backend'dedir; frontend yalnız
`NEXT_PUBLIC_*` görür.

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `TARGET_API_KEY` | _(boş)_ | **Secret** — hedef API `X-Production-Key`. Yalnız backend okur. |
| `TARGET_API_URL` | `http://89.252.189.91:8983` | Hedef MES API kökü |
| `TARGET_API_SUBMIT_PATH` | `/api/v1/submit` | Gönderim path'i |
| `TARGET_API_TIMEOUT_SECONDS` | `15` | httpx timeout |
| `TARGET_API_MAX_RETRIES` | `3` | Maks. deneme |
| `TARGET_API_BACKOFF_BASE_SECONDS` | `2` | Exponential backoff tabanı (`base ** attempt`) |
| `TARGET_API_RATE_LIMIT_COOLDOWN_SECONDS` | `60` | 429 sonrası bekleme |
| `APP_ENV` / `LOG_LEVEL` | `development` / `INFO` | Ortam / log seviyesi |
| `DATABASE_URL` | `sqlite:///db/app.db` | SQLite yolu (config mutlak yolu hesaplar) |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000` | Doğrudan erişim için CORS allow-list |
| `AUTO_SEED` | `1` | İlk açılışta `production_data.csv`'i otomatik seed et |
| `NEXT_PUBLIC_API_URL` | _(boş)_ | Frontend API kökü; boş → same-origin proxy |
| `BACKEND_INTERNAL_URL` | `http://localhost:8000` | Next.js `rewrites()` proxy hedefi |

> Validasyon eşikleri (`validation_tolerance_pct`, `validation_p_suspect_upper`,
> `validation_p_impossible_upper`, `validation_outlier_z_threshold`, `validation_systemic_ratio`)
> de `Settings` (pydantic-settings) üzerinden env ile override edilebilir.

## 🔗 API Endpoint Özeti

FastAPI title: **Üretim Performans Takip API** (v0.1.0). Tüm feature endpoint'leri `/api/v1`
altındadır. `GET /health` (liveness, `{"status":"ok","env":...}`) ve `GET /` (kök) **prefix
dışındadır**.

### Imports (`/api/v1/imports`)

| Method | Path | Açıklama |
|--------|------|----------|
| POST | `/preview` | CSV önizleme (DB'ye yazmaz) → `ImportPreview` |
| POST | `/import` | CSV import (→ SQLite) → `ImportSummary` |
| GET | `/batches` | tüm batch'ler `list[BatchOut]` |
| GET | `/batches/active` | aktif batch `BatchOut \| None` |
| POST | `/batches/{batch_id}/activate` | aktif batch'i değiştir (404 yoksa) |
| DELETE | `/batches/{batch_id}` | batch sil → 204 (404 yoksa) |

### Records (`/api/v1/records`)

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/list` | filtre + sayfalama + sıralama → `PaginatedRecords` |
| GET | `/export` | filtreli UTF-8 BOM CSV stream (attachment, no-store) |
| GET | `/distinct/{column}` | bir kolonun farklı değerleri |
| GET | `/{record_id}` | tek kayıt (404 yoksa) — route sırası: `/distinct` & `/export` önce |

### Validation (`/api/v1/validation`)

| Method | Path | Açıklama |
|--------|------|----------|
| POST | `/run` | (ops. `record_ids`) motoru çalıştır → `{summary, record_count}` |
| GET | `/summary` | canlı `summarize(results)` |
| GET | `/issues` | **canlı** issue listesi (kategori/severity/rule_id/record_status filtreleri) — tablodan değil, `run_validation`'dan üretilir |
| GET | `/report` | tam `full_report(results)` |
| POST | `/records/{id}/fix` | patch uygula, `status='valid'`, audit |
| POST | `/records/{id}/reject` | `status='rejected'`, audit |
| POST | `/records/{id}/accept` | `status='valid'`, audit |
| GET | `/records/{id}/edits` | audit trail (`record_edits`, edited_at desc) |

### Analytics (`/api/v1/analytics`)

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/kpis` | filtreli KPI dict |
| GET | `/oee-trend` | OEE zaman serisi (`days` 1..90, default 21) |
| GET | `/shift-comparison` · `/station-ranking` · `/quality-distribution` | kırılım listeleri |
| GET | `/recent-records` · `/top-stations` · `/problem-shifts` | dashboard tabloları (`batch_id`, `limit`) |
| GET | `/filter-options` | `{stations, stock_names, work_centers}` |

### Sync (`/api/v1/sync`)

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/preview` | gönderilecek (gün, vardiya) gruplarının önizlemesi → `SyncPreview` |
| POST | `/submit` | **202 Accepted** — arka planda gönder; `targets[]` ile çoklu-grup hedefleme |
| GET | `/history` | gönderim geçmişi (`status` filtresi, `limit`, id desc) |
| POST | `/{submission_id}/retry` | senkron yeniden gönder (404 yoksa; success ise değişmez) |

**`/submit` gövdesi** `SubmitRequest`:
`{production_date?, shift?, targets?: [{production_date, shift}], force=false}`.
Hedefleme önceliği: `targets[]` doluysa **yalnız** o gruplar; değilse `production_date` **ve**
`shift` verildiyse o tek grup; aksi halde **tüm** geçerli gruplar.
**Yanıt** `SubmitResponse`:
`{accepted: list[str], skipped_already_success: list[str], rejected_due_to_hash_conflict:
list[str], submission_ids: list[int]}` — string listeler `idempotency_key` (ör. `'2025-11-05:1'`)
tutar; `submission_ids` ayrı `list[int]`'tir.

## 🔍 Tespit Edilen Hata Tipleri

6 kategoride **43 kural** (her biri: kimlik, severity, önerilen aksiyon, gerekçe + örnek).
Dağılım: **missing 7 + range 10 + consistency 10 + duplicate 4 + format 6 + domain 6 = 43**.
**Tam katalog:** [`.docs/shared/domain/validation-rules.md`](.docs/shared/domain/validation-rules.md).

### A. Eksik / Boş Veri (`missing`) — 7 kural

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-M01 | `record_id` boş | error | reject | `record_id=""` |
| V-M02 | `Tarih` boş | error | reject | API `production_date` zorunlu |
| V-M03 | `Vardiya` boş | error | reject | gruplama yapılamaz |
| V-M04 | `İş İstasyon Adı` boş | error | reject | temel boyut |
| V-M05 | `Üretilen Miktar` boş | error | reject | çekirdek metrik |
| V-M06 | OEE bileşenlerinden biri eksik | warning | fix | formülden yeniden hesapla |
| V-M07 | Opsiyonel boyut boş (stok/iş merkezi) | warning | warn | işaretle, reddetme |

### B. Aralık Dışı (`range`) — 10 kural

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-R01 | A < 0 veya > 100 | error | reject | `A=120` |
| V-R02 | Q < 0 veya > 100 | error | reject | `Q=-5` |
| V-R03 | OEE < 0 veya > 100 | error | reject | `OEE=140` |
| V-R04 | P < 0 | error | reject | negatif performans imkânsız |
| V-R05 | 100 < P ≤ 150 | warning | warn | idealin üstünde, şüpheli |
| V-R06 | P > 150 | error | reject | fiziksel olarak imkânsız |
| V-R07 | Üretilen < 0 | error | reject | `produced_qty=-3` |
| V-R08 | Hatalı < 0 | error | reject | `scrap_qty=-1` |
| V-R09 | Süre alanlarından biri < 0 | error | reject | `run_time=-2` |
| V-R10 | Vardiya ∉ {1,2,3} | error | reject | `shift=4` |

> V-R05/V-R06 eşikleri ayarlanabilir: `validation_p_suspect_upper` (100.0) ve
> `validation_p_impossible_upper` (150.0).

### C. Tutarsız İlişki (`consistency`) — 10 kural (en kritik + en çok puan)

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-C01 | Fire > Üretim | error | reject | Üretim=100, Fire=130 |
| V-C02 | \|OEE − A·P·Q/10000\| > 1.0 | warning | warn | OEE=82, A·P·Q/10000=78.4 |
| V-C03 | \|Q − (Ü−H)/Ü·100\| > 1.0 | warning | warn | Q=98, hesap=96.2 |
| V-C04 | \|A − Çalışma/(Çalışma+Plansız)·100\| > 1.0 | warning | warn | sürelerle uyumsuz |
| V-C05 | \|Duruş − (Planlı+Plansız)\| > 1.0 | warning | warn | bileşenler tutarsız |
| V-C06 | Üretim>0 ama Çalışma=0 | error | reject | çalışmadan üretim imkânsız |
| V-C07 | Çalışma>0, Üretim=0, Duruş=0 | warning | warn | sensör kopuk olabilir |
| V-C08 | Q=100 ama Hatalı>0 | error | reject | %100 kalite + fire çelişkisi |
| V-C09 | A=100 ama Plansız>0 | warning | warn | tam kullanılırlık + plansız duruş |
| V-C10 | OEE>0 ama Üretim=0 | warning | warn | üretim yokken OEE>0 |

> Tolerans (`validation_tolerance_pct`, default 1.0): V-C02/C03/C04/C05 iki yüzde değerinin
> **mutlak farkını** bu eşikle karşılaştırır (yüzde-puan toleransı).

### D. Duplicate (`duplicate`) — 4 kural

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-D01 | `row_hash` zaten DB'de | error | reject | birebir tekrar |
| V-D02 | Aynı (tarih, vardiya, istasyon, iş emri) farklı metrik | warning | warn | çelişen kayıt (**batch-pass**) |
| V-D03 | Aynı `record_id` ≥ 2 satırda | error | reject | PK tekrarı |
| V-D04 | Aynı `file_hash` daha önce import | warning | warn | dosya tekrarı |

### E. Format (`format`) — 6 kural

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-F01 | Tarih ISO değil | info | fix | `11/5/2025` → `2025-11-05` |
| V-F02 | Ondalık ayraç virgül | info | fix | `87,3` → `87.3` |
| V-F03 | A/P/Q 0–1 ölçeğinde | warning | fix | `0.87` → `87.0` (toplu) |
| V-F04 | `work_order_no` `^302\d{7}$` dışı | warning | warn | `302ABC1234` |
| V-F05 | String trim/case tutarsız | info | fix | `  IMM-2700-3 ` → `imm-2700-3` |
| V-F06 | `station_name` `IMM-####-#` dışı | info | warn | `MAC-123` |

### F. Domain / Fiziksel İmkânsız (`domain`) — 6 kural

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-X01 | `prod_date` gelecek | error | reject | `2026-12-01` |
| V-X02 | Rapor penceresi dışı (5–25 Kas 2025) | warning | warn | `2024-01-01` |
| V-X03 | Çalışma + Duruş > 1440 dk | error | reject | 1500 dk/gün |
| V-X04 | Plansız > (Çalışma + Plansız) | error | reject | duruş toplamdan büyük |
| V-X05 | Üretim miktarı istatistiksel outlier (\|z\|>3) | warning | warn | doğal mı anomali mi? (**batch-pass**) |
| V-X06 | OEE=0 ama tam üretim+çalışma | warning | warn | ölçüm hatası olabilir |

> **Statü = severity'den türetilir:** herhangi ERROR → `rejected`; yoksa WARNING → `suspect`;
> aksi halde `valid`. **Outlier politikası:** istatistiksel tespit → `warning`, otomatik
> reddedilmez (case FAQ: "doğal outlier'lar hata mı?").
> **Sistemik vs tekil:** bir rule_id, kayıtların ≥ `validation_systemic_ratio` (0.2) oranında
> görülürse raporda "sistemik" sınıflanır.

## 🔌 API Entegrasyon Akışı

Yalnız **`status='valid'`** kayıtlar, **(gün, vardiya) bazında agrege** edilip hedef API'ye
POST edilir. Hatalı/şüpheli kayıt asla gitmez.

```
1. preview   GET  /api/v1/sync/preview        gönderilecek (gün,vardiya) payload'ları göster
2. submit    POST /api/v1/sync/submit          202 → arka planda gönder (idempotent, retry)
3. history   GET  /api/v1/sync/history         her gönderim: durum, http kodu, submission_id
4. retry     POST /api/v1/sync/{id}/retry       failed/retrying → senkron yeniden dene
```

- **Auth:** `X-Production-Key` (yalnız `.env` → backend; frontend/log/response'ta asla; log'da
  `***REDACTED***`).
- **Idempotency:** `idempotency_key = "{YYYY-MM-DD}:{shift}"` (DB unique) + `payload_hash`
  (canonical JSON SHA-256). Aynı key + aynı hash success → `skipped_already_success`; farklı hash
  + `force=false` → `rejected_due_to_hash_conflict`; `force=true` → yeni pending oluşturulur.
- **Retry matrisi:** retry edilen → **429** (60s cooldown) + **5xx** (500/502/503/504) + ağ/timeout
  (httpx Timeout/Connect/RemoteProtocol). **Kalıcı hata (retry yok):** **401 / 422 / 413**.
  Backoff `base ** attempt` (base=2), `max_retries=3`, `timeout=15s` — hepsi config-driven.
- **Çoklu hedef:** `targets: [{production_date, shift}]` ile birden çok (gün, vardiya) grubu tek
  istekte hedeflenebilir; `shift` yalnız {1,2,3} olabilir (aksi halde 422).
- **Async:** `/submit` 202 döner; teslimat `BackgroundTasks` ile arka planda, kendi DB session'ında.
- **Detay:** [`.docs/shared/api-contract/target-api.md`](.docs/shared/api-contract/target-api.md).

## ✅ Test & Kalite

`backend/tests/` 5 dosya, toplam **38 geçen pytest testi** (`make test`):

| Dosya | Kapsam |
|-------|--------|
| `test_oee.py` | 6 test — `recompute_oee`: A·P·Q formülü, P>100 cap, sıfır üretim → 0.0, tam boş → None, eksik P → None, fire>üretim → Q=0 |
| `test_ingestion.py` | 11 test — normalizer (4 tarih formatı, ondalık, yüzde rescale, trim/case, kolon map) + import_csv (success, duplicate-file, parse-failed, missing-required, row-hash dedupe, seed `>2000` satır) |
| `test_sync.py` | 7 test — aggregator group-by (idempotency_key), mock client 200/401/422, retry (429/500/503 retry; 401/422/413 değil), secret payload'da yok, payload-hash idempotency |
| `test_validation.py` | parametrik 12 kural (pozitif/negatif) + 2 uçtan uca motor testi (statü ataması, batch V-D02/V-X05) |
| `conftest.py` | izole temp-file SQLite engine, session, autouse temizleme, FastAPI `TestClient`, örnek 18-kolon CSV |

> **Not:** 38 test **backend**'e aittir. Frontend'de otomatik test yok — `make test-web`
> (`npm test --if-present`) bir `test` script'i tanımlı olmadığından **no-op**'tur.

**Kalite araçları:** `ruff` (Python format/lint), `eslint` (`eslint-plugin-boundaries` +
`no-explicit-any` + `process.env` yasağı), `prettier` (TS), `tsc` typecheck (`make typecheck`
yalnız frontend `tsc`'sini çalıştırır; mypy kurulu ama Makefile hedefine bağlı değil). Hepsi
`make check` altında (CI eşdeğeri).

## ⚠️ Yapamadıklarım / Vakit Yetmeyenler (dürüst)

- **Circuit breaker** yok — ardışık 429/5xx'lerde otomatik duraklatma operatöre/retry'a bırakıldı.
- **İndirilebilir validation report (Excel/PDF)** yok — sadece JSON API + UI tablo (`openpyxl`
  bağımlılığı hazır ama export yazılmadı).
- **Kural eşiklerini UI'dan düzenleme** yok — eşikler `.env` / `settings` üzerinden.
- **Tam data-lineage view'ı** yok — `import_batch_id` ile kısmi iz var, ama CSV satırı →
  production_record → sync_submission uçtan uca görselleştirmesi eksik.
- **`validation_issues` tablosu kullanılmıyor** — issue'lar canlı `run_validation`'dan üretilir,
  tabloya yazılmaz. Sonuç olarak `records` özelliğindeki `issue_count` ve `has_issues` ("Sadece
  sorunlu") filtresi bu boş tabloyu okuduğu için **fiilen etkisizdir**; "sorunlu" ayrımı pratikte
  `validation_status` (suspect/rejected) üzerinden yapılmalı. (İleride: ya tabloyu doldur ya da
  bu filtreyi statü-tabanlı yap.)
- **Çoklu dil (i18n)** yok — UI tamamen Türkçe.
- **Auth (kullanıcı girişi)** yok — tek-kişilik operatör aracı varsayımı (`edited_by` audit'i var, login UI'sı yok).
- **DB şema migration** Alembic ile değil, yalnız `init_db.create_all` — şema evrimi için geçiş script'leri gerekli.
- **CI/CD pipeline** (GitHub Actions vb.) repo düzeyinde yok — manuel `make check`.
- **Prod deploy / konteynerleştirme** yok — case kapsamı gereği yalnız yerel çalıştırma hedeflendi.
- **100K+ satır performans** profili yapılmadı — senkron SQLAlchemy + tek seferlik import yeterli görüldü.

## 🌟 Daha Fazla Zaman Olsaydı

- **43 kuralın tamamı için pozitif/negatif pytest** (şu an 12 kural parametrik + 2 motor testi var → tüm kataloğa genişlet).
- **İndirilebilir Excel/PDF validation report** (`openpyxl` zaten requirements'ta).
- **Circuit breaker** (son 60s'de ≥5 hata → otomatik duraklat).
- **Tam data-lineage görselleştirme** (record_id → batch_id → submission_id grafiği).
- **Delta import** (yalnızca yeni satırları ekle) — çoklu-CSV birleştirme zaten yapıldı, sıradaki adım delta.
- **UI'dan kural eşiği düzenleme** (settings canlı reload).
- **Çoklu dil** (TR/EN) + **Auth / çok-kullanıcı** (audit zaten var).
- **Alembic migration + CI/CD + container deploy** ve **100K+ satır** performans testi (chunk + async).

## 🤖 AI Kullanımı

Bu proje AI desteğiyle geliştirilmiştir; tüm etkileşimler şeffaf biçimde
[`ai_usage/`](ai_usage/) altında belgelenir (case study §8).

- **Prompt log'ları:** [`ai_usage/prompts/`](ai_usage/prompts/) (her prompt için ayrı MD; `make ai-prompt name=<konu>`).
- **Genel envanter:** [`ai_usage/00_overall_summary.md`](ai_usage/00_overall_summary.md).
- **Transcript'ler:** [`ai_usage/transcripts/`](ai_usage/transcripts/) (claude / minimax / opencode).
- **Ekran görüntüleri:** [`ai_usage/screenshots/`](ai_usage/screenshots/).
- **Otomasyon:** `make ai-backup` → transcript'leri topla + `ai_usage/`'i güncelle.
- **Senkron guard:** `AGENTS.md` ↔ `CLAUDE.md` (`make ai-sync`).

## 📚 Dokümantasyon & Plan

- Mimari & dökümanlar → [`.docs/`](.docs/)
- Faz planı → [`.roadmap/roadmap.md`](.roadmap/roadmap.md)
- İlerleme (yapıldı/yapılmadı) → [`.roadmap/CHECKLIST.md`](.roadmap/CHECKLIST.md)
- Validasyon kural kataloğu → [`.docs/shared/domain/validation-rules.md`](.docs/shared/domain/validation-rules.md)
- Hedef API kontratı → [`.docs/shared/api-contract/target-api.md`](.docs/shared/api-contract/target-api.md)
- Mimari kararlar → [`.docs/shared/decisions/`](.docs/shared/decisions/)

---

_Teslim: `tunahan.ozturk@magna.com`_
