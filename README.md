# Üretim Performans Takip Uygulaması

> MAGNA — Mühendislik Aday Değerlendirme Case Study · **Aday: Umut Arda Özdeş**
> Otomotiv yan sanayi (enjeksiyon kalıplama) hattı için OEE & üretim kalite takip uygulaması.

[![Durum](https://img.shields.io/badge/durum-aktif-success)]() &nbsp;
Stack: **Next.js + shadcn/ui** · **FastAPI** · **SQLite** &nbsp; · &nbsp;
[API Swagger](http://localhost:8000/docs) &nbsp; · &nbsp;
[Tam kural kataloğu](.docs/shared/domain/validation-rules.md)

---

## 📌 Projenin Amacı

MES sisteminden gelen `.csv` üretim raporlarını içe aktaran, **veri kalitesini doğrulayan**,
OEE/üretim/fire/duruş metriklerini raporlayan ve **yalnızca doğrulanmış veriyi** merkezi sisteme
REST API ile gönderen tam-stack web uygulaması. Excel'de manuel, hataya açık ve yavaş olan süreci
otomatikleştirir.

Kapsam: **2.117 satır · 18 kolon · 21 gün** (5–25 Kasım 2025) gerçekçi MES verisi üzerinde uçtan
uca doğrulama + gönderim.

## ⚙ Hızlı Kurulum (3 komuttan az)

```bash
git clone https://github.com/<kullanici>/umut-arda-ozdes-uretim-takip-case.git
cd umut-arda-ozdes-uretim-takip-case
make setup            # .env kopyalar + backend venv + frontend npm kurar
```

> Ardından `.env` içindeki `TARGET_API_KEY`'i case'ten gelen gerçek key ile doldurun.
> `data/production_data.csv` dosyası repoda hazır (gitignore'lı değil — case'in runtime verisi).

## ▶ Çalıştırma

```bash
make dev              # web → http://localhost:3000   ·   api → http://localhost:8000/docs
```

| Komut | İş |
|-------|----|
| `make dev-api` / `make dev-web` | tek servis |
| `make db-init` / `make seed` | DB şeması / örnek veri import |
| `make test` | testler (özellikle validasyon) |
| `make check` | lint + typecheck + test (CI eşdeğeri) |
| `make ai-backup` | AI transcript + prompt loglarını `ai_usage/` altına topla |
| `make help` | tüm komutlar |

## ⚙️ Mimari Kararlar

| Karar | Seçim | Kısa Gerekçe |
|-------|-------|--------------|
| Frontend framework | **Next.js 14 (App Router) + TypeScript** | "Tercih edilen" React; SSR + route grupları; `next.config.mjs` üzerinden API proxy. |
| UI kütüphanesi | **shadcn/ui + Tailwind** | Semantic token sistemi (`bg-card`, `text-oee-good`, …) → hardcoded renk yok, dark mode bedava. |
| State | **TanStack Query (server) + Zustand (UI)** | Server-cache vs UI-state ayrımı; refetchInterval ile sync geçmişi canlı. |
| Grafik | **Recharts** | Declarative, shadcn/tailwind token'larıyla uyumlu. |
| Backend framework | **FastAPI + Pydantic v2** | Otomatik OpenAPI/Swagger + birinci sınıf validasyon. |
| Veritabanı | **SQLite + SQLAlchemy 2.0 (Mapped[])** | Case zorunluluğu; ORM ile tip güvenliği + async olmayan senkron session yeterli. |
| HTTP client | **httpx + tenacity** | Senkron + retry/backoff; hedef API için `X-Production-Key` sadece backend'de. |
| CSV işleme | **pandas** | Normalize (tarih/ondalık/yüzde ölçeği) + groupby agregasyon. |
| Feature organizasyon | **feature izolasyonu (ESLint boundaries)** | Cross-feature import yok; ortak kod `shared/` (components/lib/hooks/stores/types). |
| Monorepo | **apps/* + packages/* workspaces** | Tek repo, tek setup, atomik commit. |

> Detaylı karar belgeleri: [`.docs/shared/decisions/`](.docs/shared/decisions/).

## 🖼 Ekran Görüntüleri

> Case teslim sonrası bu bölüme 4 ekran görüntüsü eklenecek (case §8 kuralı:
> ekran görüntüleri [`ai_usage/screenshots/`](ai_usage/screenshots/) altında etiketli).

- Dashboard (KPI + 4 grafik) — _(eklenecek)_
- Import & önizleme — _(eklenecek)_
- Validation report (sorunlu liste + düzelt/reddet/onayla) — _(eklenecek)_
- Hedef API gönderim ekranı + geçmiş tablosu — _(eklenecek)_

## 🔍 Tespit Edilen Hata Tipleri

6 kategoride **47 kural** (her biri: kimlik, severity, önerilen aksiyon, gerekçe + örnek).
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

### D. Duplicate (`duplicate`) — 4 kural

| ID | Koşul | Sev | Aksiyon | Örnek |
|----|-------|-----|---------|-------|
| V-D01 | `row_hash` zaten DB'de | error | reject | birebir tekrar |
| V-D02 | Aynı (tarih, vardiya, istasyon, iş emri) farklı metrik | warning | warn | çelişen kayıt |
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
| V-X05 | Üretim miktarı istatistiksel outlier (\|z\|>3) | warning | warn | doğal mı anomali mi? |
| V-X06 | OEE=0 ama tam üretim+çalışma | warning | warn | ölçüm hatası olabilir |

> Tolerans: float çapraz kontrollerde **±1.0 yüzde puan** (settings'ten ayarlanabilir).
> **Outlier politikası:** istatistiksel tespit → `warning` olarak işaretlenir, otomatik
> reddedilmez (case FAQ: "doğal outlier'lar hata mı?").

## 🔌 API Entegrasyon Akışı

Yalnız **`status='valid'`** kayıtlar, **(gün, vardiya) bazında agrege** edilip hedef API'ye
POST edilir.

```
1. preview   GET  /api/v1/sync/preview         gönderilecek (gün,vardiya) payload'ları göster
2. submit    POST /api/v1/sync/submit           arka planda gönder (idempotent, retry)
3. history   GET  /api/v1/sync/history          her gönderim: durum, http kodu, submission_id
4. retry     POST /api/v1/sync/{id}/retry        failed/retrying → yeniden dene
```

- **Auth:** `X-Production-Key` (sadece `.env` → backend; **frontend/log/response'ta asla**).
- **Idempotency:** `idempotency_key = "{YYYY-MM-DD}:{shift}"` (DB unique) + `payload_hash`
  (SHA-256 of canonical JSON). Aynı key + aynı hash → skip; farklı hash → `force` bayrağı.
- **Retry:** sadece **429 (60s cooldown)** + **5xx** (exponential backoff, max 3).
  401/422/413 → **kalıcı hata**, retry yok, kullanıcıya net mesaj.
- **Async:** POST → `202 Accepted` + submission_id; arka plan `BackgroundTasks`.
- **Detay:** [`.docs/shared/api-contract/target-api.md`](.docs/shared/api-contract/target-api.md).

## 📦 Kullanılan Kütüphaneler & Gerekçe

| Kütüphane | Neden |
|-----------|-------|
| FastAPI | Pydantic ile birinci sınıf validasyon + otomatik OpenAPI/Swagger |
| Pydantic v2 / pydantic-settings | I/O doğrulama + `.env` secret yönetimi |
| pandas | CSV parse, normalize, agregasyon |
| SQLAlchemy 2.0 + SQLite | Zorunlu DB; `Mapped[]` tip güvenli ORM |
| httpx + tenacity | Hedef API client + retry/backoff |
| Next.js 14 + shadcn/ui + Tailwind | "Tercih edilen" React; token-tabanlı tema, erişilebilirlik |
| TanStack Query / Zustand | Server-state / UI-state ayrımı |
| Recharts | OEE trend / dağılım grafikleri |
| ESLint `boundaries` | Feature izolasyonu mimari kuralı (lint'te zorunlu) |
| ruff (Python) / Prettier (TS) | Otomatik format; CI ile aynı |
| pytest | Backend birim testleri (validasyon kuralları + ingestion edge case) |

> Detaylı kararlar: [`.docs/shared/decisions/`](.docs/shared/decisions/).

## ⚠️ Yapamadıklarım / Vakit Yetmeyenler (dürüst)

- **Validation birim testleri (pytest)** yazılmadı — kural motoru çalışıyor, kural sayısı
  (47) test altyapısı olmadan teslim edildi. **En kritik borç.** (`apps/api/tests/`
  klasörü boş, `make test` yeşil değil.)
- **UI drag-and-drop + progress bar** import için yapılmadı (POST endpoint hazır, sadece
  basit landing mesajı var).
- **İndirilebilir validation report (Excel/PDF)** yok — sadece JSON API ve UI tablo.
- **Circuit breaker** yok — ardışık 429/5xx'lerde durdurmak operatöre bırakıldı.
- **Rate-limit (429) otomatik cooldown'u** sadece 1 kez uygulanıyor; uzun süreli
  rate-limit durumlarında manuel retry butonu gerekli.
- **Kural eşiklerini UI'dan düzenleme** yok — `.env` üzerinden (settings).
- **Data lineage** (CSV satır → production_record → sync_submission izi) kısmen
  `import_batch_id` ile var, ama tam bir lineage view'ı yok.
- **Çoklu CSV birleştirme** (Faz 1 bonus) yapılmadı.
- **Çoklu dil (i18n)** — UI tamamen Türkçe, İngilizce yok.
- **Çoklu ortam profili** (dev/staging/prod) ayrımı yok; tek `.env`.
- **CI/CD pipeline** (GitHub Actions vb.) — repo düzeyinde değil, manuel `make check`.
- **Auth (kullanıcı girişi)** yok — tek-kişilik operatör aracı varsayımı.
- **DB şema migration** Alembic vb. ile değil, sadece `init_db.create_all` — şema
  evrimi için geçiş script'leri gerekli.
- **Prod deploy** (Docker/Helm) — sadece yerel `make dev` ile çalışır.

## 🌟 Daha Fazla Zaman Olsaydı

- **47 kuralın pytest'i (pozitif/negatif)** — şu an sadece smoke test.
- **İndirilebilir Excel validation report** (`openpyxl` zaten requirements'ta).
- **Circuit breaker** (son 60s'de ≥5 hata → 5 dakika duraklat).
- **100K+ satır** performans testi (chunk import + async SQLAlchemy).
- **Data lineage** görselleştirme (record_id → batch_id → submission_id grafiği).
- **Çoklu CSV** birleştirme + Delta import (sadece yeni satırları ekle).
- **UI'dan kural eşiği düzenleme** (settings'ten canlı reload).
- **Çoklu dil** (TR/EN).
- **Auth + çok-kullanıcı** (audit `edited_by` zaten var, sadece login UI'sı eksik).
- **Grafik palet tema** — şu an sabit `chart-1..5` token'ları; veri setine göre
  otomatik palette.

## 🤖 AI Kullanımı

Bu proje AI desteğiyle geliştirilmiştir; tüm etkileşimler şeffaf biçimde
[`ai_usage/`](ai_usage/) altında belgelenir (case study §8).

- **Prompt log'ları:** [`ai_usage/prompts/`](ai_usage/prompts/) (her prompt için ayrı MD).
- **Genel envanter:** [`ai_usage/00_overall_summary.md`](ai_usage/00_overall_summary.md).
- **Transcript'ler:** [`ai_usage/transcripts/`](ai_usage/transcripts/) (AI başına klasör).
- **Ekran görüntüleri:** [`ai_usage/screenshots/`](ai_usage/screenshots/).
- **Otomasyon:** `make ai-backup` → transcript'leri topla + `ai_usage/`'i güncelle.
- **Senkron guard:** `AGENTS.md` ↔ `CLAUDE.md` (`make ai-sync`).

## 📚 Dokümantasyon & Plan

- Mimari & dökümanlar → [`.docs/`](.docs/)
- Faz planı → [`.roadmap/roadmap.md`](.roadmap/roadmap.md)
- İlerleme (yapıldı/yapılmadı) → [`.roadmap/CHECKLIST.md`](.roadmap/CHECKLIST.md)
- Validasyon kural kataloğu → [`.docs/shared/domain/validation-rules.md`](.docs/shared/domain/validation-rules.md)
- Hedef API kontratı → [`.docs/shared/api-contract/target-api.md`](.docs/shared/api-contract/target-api.md)

---

_Teslim: `tunahan.ozturk@magna.com`_
