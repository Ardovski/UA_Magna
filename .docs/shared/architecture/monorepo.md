# Mimari — Proje Yapısı

Sade, tek repo: kökte `backend/` (FastAPI) + `frontend/` (Next.js) gerçek klasörleri,
feature-bazlı `src/` / `app/features/`, gruplu `.docs/`.

## Neden tek repo (sade kök)?
- Frontend + backend tek repoda → tek `make setup`, tek README, atomik commit'ler.
- Kök sade: yalnız `backend/ frontend/ data/ db/ scripts/ ai_usage/` + zorunlu config dosyaları.
- Case study'nin "3 komuttan az kurulum" şartını kolaylaştırır.

## Tam Ağaç

```
umut-arda-ozdes-uretim-takip-case/
├── backend/                          # FastAPI backend (Python)
│   ├── main.py                       # `uvicorn main:app` shim → app.main:app
│   ├── app/
│   │   ├── main.py                   # uygulama girişi, router mount, middleware
│   │   ├── core/                     # config (.env), logging, hata yönetimi
│   │   ├── db/                       # SQLAlchemy engine/session, models, init_db
│   │   ├── schemas/                  # boş placeholder; Pydantic modelleri features/*/schemas.py'de
│   │   ├── features/
│   │   │   ├── ingestion/            # CSV parse + import + duplicate
│   │   │   ├── validation/           # KURAL MOTORU (kalp) + rules/
│   │   │   ├── analytics/            # OEE recompute, KPI, trend
│   │   │   ├── records/              # filtre/sorgu/CSV export
│   │   │   └── sync/                 # hedef API client, idempotency, retry
│   │   └── api/v1/                   # HTTP router'ları (endpoint'ler)
│   ├── tests/                        # pytest (conftest.py + test_*.py, düz dosyalar)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml                # ruff/pytest/mypy konfig
├── frontend/                         # Next.js frontend (TypeScript)
│   ├── src/
│   │   ├── app/                      # App Router: / (import), /dashboard, /records, /validation, /sync
│   │   ├── components/ui/            # shadcn/ui bileşenleri
│   │   ├── features/                # import, dashboard, records, validation, sync
│   │   ├── lib/                      # api client, query client, utils
│   │   ├── hooks/                    # paylaşılan React hook'ları
│   │   ├── stores/                   # Zustand UI-state
│   │   └── types/                    # paylaşılan TS tipleri
│   ├── tailwind.config.ts            # ÖZEL DESIGN TOKEN'LARI
│   ├── components.json               # shadcn/ui konfig
│   └── next.config.mjs               # /api/v1 proxy → FastAPI
├── db/                               # SQLite veritabanının evi: app.db (gitignore'lu) + README
├── data/                             # production_data.csv (commit edilir)
├── scripts/                          # yardımcı script'ler (ai-prompt, backup vb.)
├── ai_usage/                         # AI prompt/sohbet logları (§8)
├── .docs/                            # bu dokümantasyon
├── .roadmap/                         # faz planı + CHECKLIST
├── Makefile · README.md · CLAUDE.md · AGENTS.md · .env.example · package.json
```

## Workspaces
Kök `package.json` → `workspaces: ["frontend"]`. Backend ayrı Python venv
(`backend/.venv`) kullanır; npm workspace'e dahil değildir (yalnız frontend).

## Notlar
- `backend/main.py` ince bir shim'dir: `from app.main import app`. Böylece case'in
  `cd backend && uvicorn main:app` komutu da, `uvicorn app.main:app` da çalışır.
- DB yolu CWD'den bağımsız mutlak hesaplanır (`backend/app/core/config.py` → `<repo>/db/app.db`).
- Feature izolasyonu ESLint `boundaries` ile zorunlu; ortak kod `src/` altındaki `shared` alanlarında.
