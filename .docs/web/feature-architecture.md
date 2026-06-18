# Frontend Feature Mimarisi

İlke: her feature **bağımsız** (self-contained); feature'lar birbirine bağımlı değildir. Birden
fazla yerde kullanılan her şey **shared** katmanına alınır. Kurallar ESLint ile zorunlu kılınır
(bkz. [`../shared/conventions/prohibitions.md`](../shared/conventions/prohibitions.md)).

## Katmanlar ve Yön
```
app  →  feature  →  shared        (yalnız bu yön; ters yön yasak)
```
- **app** (`src/app`): sayfa kompozisyonu; feature ve shared kullanır.
- **feature** (`src/features/*`): bir iş yeteneği; **yalnızca kendi içini + shared'ı** kullanır.
- **shared**: birden fazla yerde kullanılan, tek bir feature'a ait olmayan kod.

## Feature İçi Yapı (public API)
```
src/features/<feature>/
├── index.ts            # PUBLIC API — dışarıya yalnız buradan açılır
├── <Feature>Page.tsx   # ve diğer feature'a özel bileşenler (PascalCase.tsx)
├── use<Feature>.ts     # TanStack Query hook'ları (FastAPI çağrıları burada)
├── types.ts            # feature'a özel tipler
└── (örn. mergeSummaries.ts gibi yardımcılar)
```
Yapı **düz** (flat): bileşenler, hook'lar ve yardımcılar `components/`/`hooks/`/`api/` alt
dizinleri olmadan doğrudan feature kökünde durur; FastAPI çağrıları ayrı bir `api/` klasörü yerine
`use*.ts` hook'larının içinde yapılır.

Dışarıdan kullanım: `import { X } from "@/features/<feature>"` (index üzerinden). Derin import
(`@/features/<feature>/<Bileşen>...`) **yasak**.

## Shared Yapısı (ortak)
| Dizin | İçerik |
|-------|--------|
| `components/ui` | shadcn/ui primitifleri |
| `components` | birden fazla feature'ın paylaştığı domain bileşenleri |
| `lib` | api client, env, utils, query-keys, constants |
| `hooks` | genel (feature'dan bağımsız) hook'lar |
| `stores` | global UI-state (Zustand) |
| `types` | paylaşılan domain tipleri |

## Karar Senaryoları: "X nereye gider?"
| Senaryo | Yer |
|---------|-----|
| Yalnız bir feature kullanıyor | o feature içinde |
| İki+ feature kullanıyor | **shared** |
| shadcn bileşeni | `components/ui` |
| FastAPI çağrısı (feature'a özel) | `features/<f>/use*.ts` hook'u |
| Ortak yardımcı (örn. `formatDate`) | `lib` |
| Paylaşılan domain tipi (`ProductionRecord`) | `types/domain.ts` |
| İki feature'ın paylaştığı filtre state (dashboard + records) | `stores` |
| İki feature aynı bileşeni kullanacak | kopyalama; **shared/components'e taşı** |

## Neden Bu Kurallar?
- Bir feature silinebilir/taşınabilir, diğerlerini kırmaz.
- Döngüsel bağımlılık oluşmaz.
- Ortak kod tek yerde (kopya yok) → tutarlılık.
- İhlal anında ESLint hatası: `boundaries/element-types`, `import/no-cycle`,
  `no-restricted-imports` (bkz. prohibitions.md).

## Backend Karşılığı
Backend de feature-bazlıdır (`app/features/*`): ingestion, validation, analytics, records, sync.
Ortak altyapı `app/core` (config, logging, errors) ve `app/db`'dedir. Bkz.
[`../api/architecture.md`](../api/architecture.md).
