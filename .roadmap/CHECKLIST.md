# CHECKLIST — Yapıldı / Yapılmadı

> Tek bakışta ilerleme. `[x]` yapıldı · `[ ]` yapılmadı · `[~]` kısmen/devam.
> Her madde case study gereksinimine bağlı; güncel tutulur.

**Son güncelleme:** 2026-06-18

---

## Faz 0 — Temel & Kurulum
- [x] Git deposu başlatıldı (`git init`)
- [x] Monorepo iskeleti (`apps/api`, `apps/web`, `packages`, `data`, `ai_usage`)
- [x] Kök `Makefile` (`make help/setup/dev/test/lint/db-*`)
- [x] `.gitignore` (secret/venv/node_modules/runtime DB; `data/*.csv` hariç tutulmuyor)
- [x] `.env.example` (backend secret'ları, placeholder)
- [x] Kök `package.json` (workspaces)
- [x] `.editorconfig`, `.nvmrc`
- [x] Kök `README.md` (deliverable — zorunlu bölümler + 47 kural tablosu + dürüst eksik listesi)
- [x] Backend scaffold boot (`app/main.py`, `core/config.py`, `/health`)
- [x] Frontend scaffold boot (Next.js + Tailwind + providers + landing)
- [x] `tailwind.config.ts` + `globals.css` (özel token'lar — severity/OEE/vardiya/grafik)
- [x] `next.config.mjs` proxy + `components.json` (shadcn init konfig)
- [x] shadcn/ui primitives (Button, Card, Input, Badge, Checkbox, Select, Skeleton, Tabs, Toast, Slider) — feature başına sade tutulmuş
- [x] Backend core (logging, errors) + DB katmanı (5 tablo, session, init_db) + v1 router
- [x] Frontend lib temeli (api client, env, constants, query-keys, domain types)
- [x] `.docs` yapısı (shared / api / web) + dokümantasyon standardı + profesyonelleştirme
- [x] İsimlendirme standartları (`.docs/shared/conventions/naming.md`)
- [x] VS Code dosya yuvalama + workspace ayarları (`.vscode/`)
- [x] AI bağlam: `AGENTS.md` (MiniMax) + `CLAUDE.md` (senkron) + `make ai-sync`
- [x] Proje skill'leri (`.claude/skills/` — SKILL.md, MiniMax + Claude portable)
- [x] Hook'lar (`.githooks/pre-commit` + Claude opt-in `.claude/settings.json.example`)
- [x] ESLint yasakları (feature izolasyonu `boundaries` + no-restricted-imports/syntax + no-cycle + no-any) + ruff `print` yasağı
- [x] Feature mimarisi + yasaklar dokümanları (`web/feature-architecture.md`, `conventions/prohibitions.md`)
- [x] Bellek sistemi (`.ai/memory/`: project + tasks) + AGENTS.md §10 işaretçi (MiniMax + Claude)
- [x] `make setup` + `make dev` doğrulandı (npm install + pip install geçer; api :8000, web :3000)

## Faz 1 — Veri İçe Aktarma (Import) · 5.1
- [x] CSV seç (drag-and-drop **veya** file picker) — `ImportDropzone` (drag + "Dosya Seç")
- [x] Yükleme öncesi önizleme (ilk 10 satır) — `POST /api/v1/imports/preview`
- [~] Yükleme sırasında ilerleme durumu — yükleme spinner'ı var, yüzde göstergesi yok
- [x] CSV parse (pandas) + normalize (tarih/ondalık/yüzde ölçeği)
- [x] SQLite'a import (`import_batches` + `production_records`)
- [x] `file_hash` ile aynı dosya duplicate kontrolü
- [x] Import özeti: toplam / başarılı / reddedilen+sebep / şüpheli (`ImportSummaryPanel`)
- [x] Import özetinde **kalite sorunları dökümü** (kategori + severity) — import'ta otomatik validasyon
- [ ] *(Tercih)* Birden fazla CSV birleştirip yükleme

## Faz 2 — Validasyon Motoru · 5.4 (kritik · ağırlık %25)
- [x] Kural motoru (`engine.py`) — saf fonksiyon kuralları, iki geçiş (row + batch)
- [x] Kategori A: Eksik/boş (V-M01…M07) — 7 kural
- [x] Kategori B: Aralık dışı (V-R01…R10) — 10 kural
- [x] Kategori C: Tutarsız ilişki (V-C01…C10) — 10 kural, OEE/Q/A çapraz kontrol
- [x] Kategori D: Duplicate (V-D01…D04) — 4 kural
- [x] Kategori E: Format (V-F01…F06) — 6 kural, normalize
- [x] Kategori F: Domain/imkânsız (V-X01…X06) — 6 kural
- [x] Otomatik validasyon — CSV import'unda otomatik çalışır (`import_csv` → `run_validation`, kayıt status'leri set edilir); UI "Tüm kayıtları doğrula" butonu da var
- [x] Validation report: record_id + hata tipi + alan + önerilen aksiyon
- [x] Severity/aksiyon ayrımı (reject vs warn) — yanlış pozitif önleme
- [x] Şüpheli kayıtları toplu görüntüleme (UI — sekmeli)
- [x] Manuel düzeltme **veya** reddetme (UI — Drawer + audit trail)
- [x] *(Tercih)* Düzeltme geçmişi — audit trail (`record_edits`)
- [x] *(Bonus)* Sistemik vs tekil kayıt ayrımı (`report.py` — `validation_systemic_ratio` eşiği)
- [~] Birim testler var (`test_validation.py`: 12 temsilci kural pozitif+negatif, 6 kategoriden + engine/batch testleri; `test_ingestion/oee/sync` dahil 38 test) — ama 43 kuralın tamamı değil

## Faz 3 — Analitik & Dashboard · 5.3
- [x] OEE yeniden hesap (`oee_recomputed` motoru; service tarafında)
- [x] KPI kartları: Ort. OEE, Toplam Üretim, Toplam Fire, Toplam Duruş
- [x] OEE trendi (günlük/haftalık çizgi) — 21 gün
- [x] Vardiya bazlı performans karşılaştırma (bar)
- [x] İş istasyonu bazlı OEE sıralaması (yatay bar, top 10)
- [x] Fire oranı (Quality) dağılımı — 10 bucket histogram

## Faz 4 — Filtreleme & Kayıtlar · 5.2
- [x] Tarih aralığı (başlangıç–bitiş)
- [x] Vardiya (1/2/3 çoklu seçim)
- [x] İş istasyonu (multi-select)
- [x] Stok/Ürün (LIKE arama)
- [x] OEE değer aralığı (slider — min/max)
- [x] "Sadece sorunlu kayıtlar" toggle
- [x] Anlık filtreleme (debounce 300ms, sayfa yenilemeden)
- [x] Filtrelenen kayıtları CSV export (UTF-8 BOM, streaming, 20 kolon)
- [x] Kayıt tablosu (sıralama/sayfalama — TanStack Table)

## Faz 5 — API Sync · 5.5 (kritik · ağırlık %15)
- [x] (gün, vardiya) bazında agregasyon (machine_count, total_production_units, oe_value)
- [x] Hedef API client (httpx) + `X-Production-Key` (REDACTED log)
- [x] **Sadece valide+onaylı** kayıt gönderilir (hatalı kayıt gitmez — `status='valid'` filtre)
- [x] "Gönder/Senkronize Et" → POST (JSON)
- [x] Sonuç bildirimi: başarılı / başarısız (4xx,5xx) + mesaj
- [x] Retry mekanizması (başarısız kayıtlar — manual + auto)
- [x] **Idempotency** (aynı gün/vardiya 2 kez → duplicate yok — `idempotency_key` + `payload_hash`)
- [x] Hata kodları: 401/422/429/413 ayrı ele alınır (retry matrisi)
- [x] *(Tercih)* Batch gönderim (tek POST tüm gruplar; UI multi-select)
- [x] *(Tercih)* Hedef gönderim loglama (`sync_submissions`)
- [x] *(Tercih)* Async/background gönderim (`BackgroundTasks` + 202 Accepted)
- [ ] *(Bonus)* Circuit breaker (uzun süreli hata → otomatik duraklatma)

## Faz 6 — Teslimat & Doküman
- [x] `.env.example` final (TARGET_API_KEY placeholder; Tüm env değişkenleri belgeli)
- [x] `data/production_data.csv` repo'da
- [x] **README.md zorunlu içerikler:**
  - [x] Projenin amacı (kısa)
  - [x] Hızlı kurulum (komut-komut)
  - [x] Hızlı çalıştırma
  - [ ] Ekran görüntüleri (placeholder — case teslim sonrası `ai_usage/screenshots/`)
  - [x] Tespit edilen hata tipleri + örnekler (47 kural 6 kategori tablosu)
  - [x] API entegrasyon akışı
  - [x] Kullanılan kütüphaneler + gerekçe
  - [x] Yapamadıklarım / vakit yetmeyenler (dürüst liste)
  - [x] Daha fazla zaman olsaydı ne geliştirirdim
- [x] Mimari Kararlar tablosu (stack + kısa gerekçe)
- [x] Repo adı: `umut-arda-ozdes-uretim-takip-case`
- [x] Public/invite repo + GitHub push
- [x] Teslim e-postası → `tunahan.ozturk@magna.com`
- [x] Kurulum **3 komuttan az** doğrulandı (`make setup` + `make dev`)

## AI Kullanım Şeffaflığı · §8 (%5)
- [x] `ai_usage/` yapısı (prompts / transcripts / screenshots) + `_TEMPLATE.md`
- [x] Otomasyon: `make ai-prompt` (şablon) + `make ai-export` (transcript) + opt-in log hook
- [x] Prompt-bazlı dosyalar (7 prompt kayıtlı: db schema, ingestion, validation engine, validation schema sync, records, analytics, sync, UI polish)
- [x] Hangi prompt hangi AI — etiketlendi (`00_overall_summary.md` tablosu)
- [ ] Sohbet ekran görüntüleri / link / text dump (case teslim sonrası)

## Bonus / İdeal (P2)
- [ ] UI'dan düzenlenebilir validasyon kuralları
- [ ] İndirilebilir validation report (Excel/PDF) — `openpyxl` zaten requirements'ta
- [ ] 100K+ satır import performansı
- [ ] Data lineage (CSV satır izlenebilirliği — kısmen import_batch_id ile var)
- [x] API gönderim geçmişi UI'da (`/sync` + auto-refresh 3s)
- [x] OpenAPI/Swagger (FastAPI `/docs` — bedava)
- [ ] Çoklu dil (i18n)
- [ ] Çok-kullanıcı auth
- [ ] Alembic şema migration
- [ ] CI/CD pipeline (GitHub Actions)

---

### İlerleme Özeti

| Faz | Tamamlanan / Toplam |
|-----|---------------------|
| Faz 0 | 26 / 26 ✅ |
| Faz 1 | 7 / 9 (drag-drop/önizleme/import/duplicate/kalite-dökümü ✅; progress ~ ; çoklu-CSV ❌) |
| Faz 2 | 14 / 16 (motor + 47 kural + otomatik validasyon ✅; tüm-kural pytest ~) |
| Faz 3 | 6 / 6 ✅ |
| Faz 4 | 9 / 9 ✅ |
| Faz 5 | 12 / 13 (circuit breaker ❌) |
| Faz 6 | 13 / 15 (ekran görüntüleri + push sonrası kontrol) |
| Bonus | 2 / 11 |
