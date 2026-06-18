# Dokümantasyon

Projenin teknik dokümantasyonu üç grupta tutulur: **shared** (proje geneli ve domain), **api**
(backend), **web** (frontend).

## Yapı

| Grup | İçerik |
|------|--------|
| [`shared/`](shared/) | Gereksinimler, sistem mimarisi, domain bilgisi, API sözleşmesi, kararlar, konvansiyonlar, kurulum |
| [`api/`](api/) | Backend (FastAPI): mimari, veritabanı, endpoint'ler, validasyon motoru |
| [`web/`](web/) | Frontend (Next.js): mimari, tema/token sistemi |

### shared/
| Dosya | Konu |
|-------|------|
| [`requirements/`](shared/requirements/) | Case study analizi, değerlendirme kriterleri |
| [`architecture/overview.md`](shared/architecture/overview.md) | Sistem genel bakışı, veri akışı |
| [`architecture/monorepo.md`](shared/architecture/monorepo.md) | Monorepo yapısı |
| [`domain/data-dictionary.md`](shared/domain/data-dictionary.md) | 18 kolonluk veri sözlüğü |
| [`domain/oee-formula.md`](shared/domain/oee-formula.md) | OEE formülü ve çapraz kontroller |
| [`domain/validation-rules.md`](shared/domain/validation-rules.md) | Validasyon kural kataloğu |
| [`api-contract/target-api.md`](shared/api-contract/target-api.md) | Hedef MES API sözleşmesi |
| [`conventions/`](shared/conventions/) | Kodlama, isimlendirme, dokümantasyon, **yasaklar**, AI asistan standartları |
| [`decisions/`](shared/decisions/) | Mimari karar kayıtları (ADR) |
| [`setup/`](shared/setup/) | Geliştirici onboarding, ortam değişkenleri |

### api/
| Dosya | Konu |
|-------|------|
| [`architecture.md`](api/architecture.md) | Backend katmanları, feature modülleri |
| [`database.md`](api/database.md) | SQLite şeması (6 tablo) |
| [`endpoints.md`](api/endpoints.md) | İç (internal) API endpoint'leri |
| [`validation-engine.md`](api/validation-engine.md) | Validasyon motoru implementasyonu |

### web/
| Dosya | Konu |
|-------|------|
| [`architecture.md`](web/architecture.md) | Next.js App Router, feature yapısı, durum yönetimi |
| [`feature-architecture.md`](web/feature-architecture.md) | Feature izolasyonu, shared yapısı, karar senaryoları |
| [`theme.md`](web/theme.md) | Design token sistemi (Tailwind + CSS değişkenleri) |

## İlgili
- Plan ve ilerleme: [`../.roadmap/`](../.roadmap/) — roadmap ve CHECKLIST
- AI asistan bağlamı: [`../AGENTS.md`](../AGENTS.md) (MiniMax + Claude)
- Proje skill'leri: [`../.claude/skills/`](../.claude/skills/)
- AI belleği: [`../.ai/memory/`](../.ai/memory/) (curated + görev log)
