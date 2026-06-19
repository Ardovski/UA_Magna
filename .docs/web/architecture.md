# Mimari — Frontend (Next.js + shadcn/ui)

## Stack
- **Next.js (App Router) + TypeScript** — routing + SSR/CSR
- **shadcn/ui + Tailwind** — bileşenler + token-tabanlı tema (bkz. [`theme.md`](theme.md))
- **TanStack Query** — server-state (FastAPI'den veri çekme, cache, retry)
- **Zustand** — UI-state (filtre durumu, seçili kayıtlar, modal)
- **Recharts** — OEE trend / dağılım grafikleri
- **react-hook-form + zod** — form + client-side doğrulama
- **TanStack Table** — kayıt grid'i (filtre/sıralama/sayfalama)
- **i18n (özel)** — `lib/i18n` (Context + `localStorage`) ile **TR/EN** sözlüğü (`messages.ts`); Header'daki `LanguageToggle` ile geçiş. Harici bağımlılık yok.

## Sayfa Yapısı (App Router)
```
src/app/
├── layout.tsx                       # kök layout: tema sağlayıcı, query provider
├── providers.tsx                    # client provider'lar
└── (dashboard)/                     # route group
    ├── layout.tsx                   # sidebar + uygulama kabuğu
    ├── page.tsx                     # / → Import (ImportRoute) — boş DB'de açılış akışı
    ├── dashboard/page.tsx           # Dashboard (KPI + grafikler)
    ├── records/page.tsx             # filtre + tablo + CSV export
    ├── validation/page.tsx          # şüpheli kayıtlar + düzelt/reddet + audit
    ├── sync/page.tsx                # (gün, vardiya) gönderim + retry/retry-all + geçmiş
    └── definitions/page.tsx         # Tanımlar/Definitions — veri sözlüğü + OEE + sözlük (TR/EN)
```

## Feature-bazlı Organizasyon
```
src/features/<feature>/        # DÜZ dosya yapısı (alt klasör yok)
├── index.ts                   # PUBLIC API — dışarıya yalnız buradan açılır
├── <Feature>Page.tsx          # ve diğer PascalCase bileşenler (ImportDropzone.tsx ...)
├── use<Feature>.ts            # TanStack Query hook'ları (FastAPI çağrıları burada)
├── types.ts                   # feature'a özel tipler
└── (örn. mergeSummaries.ts gibi yardımcılar)
```
Feature'lar: `import`, `dashboard`, `records`, `validation`, `sync`, `definitions`.

## API İletişimi
- `src/lib/api/client.ts` — tek tip fetch wrapper (base URL = `env.apiUrl`, `@/lib/env`'den).
  Varsayılan boş string → same-origin `/api/v1/...` çağrıları; cross-origin için `NEXT_PUBLIC_API_URL` set edilir.
  Ayrıca `api.upload` / `uploadWithProgress` (XHR ile gerçek yükleme ilerlemesi).
- `next.config.mjs` rewrites → `/api/v1/:path*` ⇒ `${BACKEND_INTERNAL_URL || http://localhost:8000}/api/v1/:path*` (same-origin proxy, CORS'suz dev).
- Tüm sunucu mutasyonları (import, fix, sync) TanStack Query `useMutation` ile.

## Sunucu-state Optimizasyonu (`providers.tsx`)
Global `QueryClient` ayarları:
- `staleTime: 60s` + `gcTime: 5dk` → aynı query 1 dakika içinde tekrar fire edilmez; unmount olunca cache 5 dakika tutulur (geri dönüşte anında döner).
- `refetchOnWindowFocus: false` → tab değişiminde gereksiz yeniden istek yok.
- `refetchOnReconnect: true` → ağ gelince otomatik tazele.
- Global `QueryCache({ onError })` + `MutationCache({ onError })` → eşleşmeyen 401/422/5xx/network hataları otomatik destructive toast. Feature sayfaları kendi mutasyonlarında zaten başarı/hata toast verir; bu köprü **sessiz kalan** hataları yakalar.
- Recharts `ResponsiveContainer` `debounce={50}` → scroll/resize sırasında re-render fırtınasını önler.
- Dashboard chart component'leri `React.memo` ile sarılı → prop değişmediği sürece re-render etmez.

## Bileşen Katmanları
1. `components/ui/*` — shadcn primitive'leri (Button, Card, Table, Dialog, Slider, Toast...).
2. `components/atoms/*` — shadcn üstü küçük bağımsız birimler (EmptyState, FieldLabel, SkeletonText, StatusDot).
3. `components/molecules/*` — 2+ atomdan oluşan, jenerik bir iş yapan birimler (SummaryCard, DiffFieldRow, KeyValueRow, ProgressBar, IssueSeverityBadge).
4. `components/organisms/*` — bağımsız anlamlı tam birimler (Header, LanguageToggle, PageHeader, DataTableShell).
5. `features/*/*.tsx` — domain bileşenleri (IssueList, OeeTrendChart, KpiCardGrid...).
6. `app/(dashboard)/**/page.tsx` — sayfa kompozisyonu.

### Katman Yönü (ESLint `boundaries/element-types` ile zorunlu)
```
app  →  feature  →  organisms  →  molecules  →  atoms  →  ui
                                                      │
                                                      └──→ shared (lib/hooks/stores/types)
```
- Ters yön **yasak** (örn. atoms → molecules import edemez).
- Feature'lar birbirini import edemez; ortak kod `shared`'a taşınır.
- `shared` (lib/hooks/stores/types) yalnız `shared` ve diğer atomlar kullanabilir; `organisms` ve `feature` shared'ı çağırabilir.

## UI/UX Öncelikleri (case %10)
- **Net hata bildirimi:** validation report tablosu (record_id, hata tipi, alan, aksiyon) +
  satır-içi renk kodu (severity token'ları → bkz. theme).
- **İlerleme geri bildirimi:** import sırasında progress, sync sırasında durum.
- **Toplu işlem:** şüpheli kayıtları toplu seç → düzelt/reddet.
- Erişilebilirlik: shadcn/Radix tabanlı (klavye + ARIA hazır).
