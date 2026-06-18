# AGENTS.md — Üretim Performans Takip Uygulaması (MAGNA Case Study)

> **Bu dosya AI kod asistanları için TEK KAYNAK (canonical) bağlamdır.** Açık standart `AGENTS.md`
> formatındadır; **MiniMax** bunu doğrudan okur.
>
> **SENKRON:** `CLAUDE.md` bu dosyanın kopyasıdır (Claude Code için). İçeriği yalnız bu dosyada
> değiştir, sonra **`make ai-sync`** çalıştır → `CLAUDE.md` güncellenir. Detay:
> [`.docs/shared/conventions/ai-assistants.md`](.docs/shared/conventions/ai-assistants.md).
>
> Detaylar için `.docs/`, plan için `.roadmap/`.

---

## 1. Proje Nedir?

Otomotiv yan sanayi (enjeksiyon kalıplama) hattı için **üretim performans ve OEE takip** web
uygulaması. MES'ten gelen `.csv` üretim raporlarını:

1. Sisteme **import** eder (CSV → SQLite)
2. **Veri kalite validasyonu** yapar (hatalı/şüpheli kayıtları tespit, sınıflandır, raporla, düzelt) ← **kritik**
3. Filtreleme + **OEE dashboard** ile raporlar
4. **Sadece temiz/onaylı** veriyi harici REST API'ye gönderir ← **2. kritik**

İşe alım case study'si (MAGNA). Aday: **Umut Arda Özdeş**. Süre: **2 iş günü**. Teslim: GitHub repo
`umut-arda-ozdes-uretim-takip-case` + e-posta `tunahan.ozturk@magna.com`.

## 2. Kritik Kurallar (asla ihlal etme)

1. **Veriyi "temiz" varsayma.** Gerçek MES verisi gibi kalite sorunları + mantıksal
   tutarsızlıklar var. Değerlendirmenin merkezi bunları yakalamaktır (**%25**).
2. **Sadece valide + onaylı kayıtlar hedef API'ye gider.** Hatalı kaydın hedefe ulaşmaması en
   kritik gereksinimlerden biridir.
3. **Secret koda gömülmez.** `TARGET_API_KEY` yalnız `.env`'den okunur. `.env` git'e girmez;
   `.env.example` paylaşılır.
4. **API gönderimi idempotent.** Aynı (tarih, vardiya) iki kez → duplicate yok. Retry/backoff zorunlu.
5. **Her hata tipini gerekçe + örnekle belgele.** Yanlış pozitif puan kaybettirir → reject (yüksek
   güven) vs warn (sezgisel) ayrımı.
6. **3 komuttan az kurulum.** `make setup && make dev` çalışmalı.
7. **AI kullanımı şeffaf.** Tüm AI sohbet/prompt'lar `ai_usage/` altında (case §8 — %5).

## 3. Stack & Gerekçe (detay: `.docs/shared/decisions/`)

| Katman | Seçim |
|--------|-------|
| Frontend | **Next.js (App Router) + TypeScript** |
| UI | **shadcn/ui + Tailwind** (özel token'lar, `tailwind.config.ts`) |
| Charts / State | Recharts · TanStack Query (server) + Zustand (UI) |
| Backend | **FastAPI** (Pydantic validasyon + otomatik OpenAPI) |
| DB | **SQLite (zorunlu) + SQLAlchemy** |
| HTTP | httpx + tenacity (retry/backoff) |

> Frontend secret tutmaz. Hedef API çağrısı (X-Production-Key) **sadece FastAPI**'de.
> Akış: Browser → Next.js → FastAPI → Hedef API.

## 4. Proje Yapısı (detay: `.docs/shared/architecture/monorepo.md`)

```
backend/   FastAPI backend  (app/features: ingestion, validation, analytics, records, sync)
frontend/  Next.js frontend (src/features: import, dashboard, records, validation, sync)
db/        SQLite veritabanı (app.db + README)   data/  production_data.csv (commit edilir)
ai_usage/  AI logları (§8)   scripts/ yardımcılar   .docs/ doküman   .roadmap/ plan + CHECKLIST
Makefile · README.md · .env.example · AGENTS.md (MiniMax) + CLAUDE.md
```

## 5. Komutlar (Makefile)

```bash
make setup      # .env kopyala + bağımlılıklar (api venv + web npm)
make dev        # api (:8000) + web (:3000)
make db-init    # SQLite şema      make seed   # CSV import
make test       # testler (özellikle validation)
make lint / format / check
make ai-sync    # AGENTS.md → CLAUDE.md (senkron)
make hooks      # git hook'ları kur (secret koruması + ai-sync)
```
Portlar: web **:3000**, api **:8000** (Swagger `/docs`).

## 6. Domain Bilgisi (detay: `.docs/shared/domain/`)

- **OEE = A × P × Q / 10000** (yüzde). A = Çalışma/(Çalışma+Plansız Duruş);
  P = ideal hıza karşı; Q = (Üretilen−Hatalı)/Üretilen.
- Kaynak: `production_data.csv` — 2.117 satır, 18 kolon, 5–25 Kasım 2025.
- 18 kolon → `.docs/shared/domain/data-dictionary.md`. Vardiya: 1 Sabah / 2 Öğle / 3 Gece.

## 7. Hedef API (detay: `.docs/shared/api-contract/target-api.md`)

- `POST {TARGET_API_URL}/api/v1/submit`, header `X-Production-Key`, body JSON.
- Gönderim **(tarih, vardiya) bazında agrege**: `{machine_count, total_production_units, oe_value, shift, production_date}`.
- Hatalar: 401 (key), 422 (detail'e bak), 429 (rate limit 1dk), 413 (>10KB).
- Idempotency key + retry/backoff → `app/features/sync/`. Tam dok: `http://89.252.189.91:8983/docs-guide`.

## 8. Konvansiyonlar

- **Dil:** Dokümanlar Türkçe; kod/identifier İngilizce.
- **Validasyon kuralları** `app/features/validation/rules/` (her kural ayrı + test). Katalog
  (kaynak doğruluk): `.docs/shared/domain/validation-rules.md`.
- İş mantığı service/feature'da; router/component ince.
- **Stil:** sadece Tailwind semantic token'ları (`.docs/web/theme.md`). Hardcoded renk yok.
- **Plan değişince** `.roadmap/CHECKLIST.md`'i güncelle (yapıldı/yapılmadı).
- Tip ipuçları zorunlu (Python public fn'ler); `any` yasak (TS).
- **Skill'ler** `.claude/skills/` (SKILL.md): tekrarlayan işler için (validasyon kuralı/feature ekleme, kalite kontrolleri).
- **Feature izolasyonu:** feature'lar birbirini import etmez; ortak kod `shared`'a. ESLint (`boundaries`) zorunlu kılar. Bkz. `.docs/web/feature-architecture.md`.
- **Yasaklar (lint zorunlu):** `.docs/shared/conventions/prohibitions.md` — `any` yok, doğrudan `process.env` yok, cross-feature import yok, hardcoded renk yok.

## 9. Yapma / Dikkat

Kaçınılması gerekenler:
- Hatalı/şüpheli kaydı hedef API'ye gönderme.
- Secret'ı koda, log'a veya frontend'e koyma.
- `data/production_data.csv`'i .gitignore'lama (runtime DB ise gitignore'lu).
- Gerekçesiz/agresif validasyon kuralı eklemek (yanlış pozitif).

Yapılması gerekenler:
- Tespit edilen her hatayı gerekçe + örnekle belgele.
- "Yapamadıklarını" README'de dürüstçe yaz.

## 10. Bellek (Memory)

- Kalıcı çalışma belleği `.ai/memory/`: `project.md` (curated kararlar/durum) + `tasks.md` (görev log).
- Görev tamamlanınca `tasks.md`'e tek satır ekle; kalıcı karar/öğreni varsa `project.md`'i güncelle.
- Yeni oturuma başlarken önce bu ikisini oku. MiniMax: `MINIMAX_MEMORY_PATH=.ai/memory`.
- **Her görev sonunda:** `tasks.md`'i güncelle + `make ai-backup` ile transcript'i tazele (§8; idempotent; `scripts/backup-sessions.sh` çalıştırır ve `ai_usage/`'i commit eder — push yapmaz; push kullanıcıya bırakılır).
- **Transcript kaynakları (`make ai-backup` hepsini tarar):** Claude Code (VS Code + CLI) `~/.claude/projects/<proje>/*.jsonl`; MiniMax (opencode CLI) `~/.local/share/opencode/opencode.db` (SQLite); eski MiniMax JSONL `~/.minimax/sessions`. Bu projeye ait **tüm** oturumlar her seferinde yedeklenir (sadece sonuncusu değil).
