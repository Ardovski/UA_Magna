# frontend — Next.js Frontend

Üretim Performans Takip arayüzü: dashboard, import, validation report, API sync.

## Çalıştırma
```bash
make dev-web          # http://localhost:3000   (kökten)
# veya: cd frontend && npm run dev
```

## Stack
Next.js (App Router) · TypeScript · **shadcn/ui + Tailwind** (özel token'lar) · TanStack Query
(server-state) · Zustand (UI-state) · Recharts · react-hook-form + zod.

## Yapı
```
src/
├── app/             # App Router; sayfalar (dashboard) route grubunda
│   ├── layout.tsx   # tema + query provider
│   ├── providers.tsx
│   ├── globals.css  # DESIGN TOKEN'LARI (CSS değişkenleri)
│   └── (dashboard)/ # / (import), /dashboard, /records, /validation, /sync
│       └── page.tsx # import (ImportRoute); dashboard → /dashboard/page.tsx
├── components/ui/   # shadcn bileşenleri (npx shadcn add ...)
├── features/        # import · dashboard · records · validation · sync
├── lib/             # api client, utils (cn, oeeColorClass)
├── hooks/ · stores/ · types/
└── tailwind.config.ts  # token → Tailwind bağlama
```

## Tema / Token
Hardcoded renk **yok**; her şey semantic token. Detay:
[`../.docs/web/theme.md`](../.docs/web/theme.md).

## shadcn bileşeni ekleme
```bash
cd frontend && npx shadcn@latest add button card table dialog badge slider
```

Mimari: [`../.docs/web/architecture.md`](../.docs/web/architecture.md)
