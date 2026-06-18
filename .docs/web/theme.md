# Mimari — Tema & Design Token Sistemi

> **İlke:** Hiçbir yerde hardcoded renk/spacing/radius yok. Her görsel değer bir **semantic
> token**'dan gelir. Token'lar `globals.css` (CSS değişkenleri) + `tailwind.config.ts`
> (`theme.extend`) ikilisinde tanımlanır. Tek kaynaktan tüm uygulama + dark mode yönetilir.

## Katmanlı Token Mimarisi

```
1. Primitive (ham)       --blue-600, --red-500 ... (ham ölçek, doğrudan KULLANILMAZ)
         atanır
2. Semantic (anlamsal)   --primary, --background, --destructive, --success ...
         Tailwind'e bağlanır
3. Component (kullanım)  bg-primary, text-success, border-severity-error ...
```

shadcn/ui konvansiyonu: semantic token'lar **HSL kanalları** olarak CSS değişkeninde tutulur
(`--primary: 222 47% 11%`), Tailwind `hsl(var(--primary))` ile sarar. Böylece opacity
modifier'ları (`bg-primary/50`) çalışır.

## `globals.css` — CSS Değişkenleri (light + dark)

```css
@layer base {
  :root {
    /* shadcn temel */
    --background: 0 0% 100%;
    --foreground: 222 47% 11%;
    --card: 0 0% 100%;
    --card-foreground: 222 47% 11%;
    --primary: 222 47% 11%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --muted: 210 40% 96%;
    --muted-foreground: 215 16% 47%;
    --accent: 210 40% 96%;
    --border: 214 32% 91%;
    --input: 214 32% 91%;
    --ring: 222 47% 11%;
    --radius: 0.5rem;

    /* --- DOMAIN SEMANTIC TOKEN'LARI (bu projeye özel) --- */
    /* Validasyon severity */
    --success: 142 71% 45%;        /* temiz / valid kayıt */
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 50%;         /* şüpheli / uyar */
    --warning-foreground: 0 0% 100%;
    --destructive: 0 72% 51%;      /* hatalı / reddet */
    --destructive-foreground: 0 0% 100%;
    --info: 217 91% 60%;           /* bilgi / düzeltildi */

    /* OEE performans bantları (world-class ≥ %85) */
    --oee-good: 142 71% 45%;       /* ≥ 85 */
    --oee-mid: 38 92% 50%;         /* 60–85 */
    --oee-low: 0 72% 51%;          /* < 60 */

    /* Vardiya renkleri */
    --shift-1: 47 95% 53%;         /* Sabah */
    --shift-2: 199 89% 48%;        /* Öğle/Gündüz */
    --shift-3: 245 58% 51%;        /* Gece */

    /* Grafik paleti (Recharts) */
    --chart-1: 222 47% 35%;
    --chart-2: 199 89% 48%;
    --chart-3: 142 71% 45%;
    --chart-4: 38 92% 50%;
    --chart-5: 280 65% 60%;
  }

  .dark {
    --background: 222 47% 7%;
    --foreground: 210 40% 98%;
    --card: 222 47% 10%;
    --card-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222 47% 11%;
    --muted: 217 33% 17%;
    --muted-foreground: 215 20% 65%;
    --border: 217 33% 20%;
    --input: 217 33% 20%;
    --ring: 213 27% 84%;
    --secondary: 217 33% 17%;
    --accent: 217 33% 17%;
    /* domain token'ları dark'ta biraz parlaklaştırılır */
    --success: 142 64% 52%;
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 58%;
    --destructive: 0 72% 58%;
    --info: 217 91% 68%;
    --oee-good: 142 64% 52%;
    --oee-mid: 38 92% 58%;
    --oee-low: 0 72% 58%;
  }
}
```

## `tailwind.config.ts` — Token Bağlama

```ts
import type { Config } from "tailwindcss";

const hsl = (v: string) => `hsl(var(--${v}) / <alpha-value>)`;

export default {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: "1.5rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        background: hsl("background"),
        foreground: hsl("foreground"),
        card: { DEFAULT: hsl("card"), foreground: hsl("card-foreground") },
        popover: { DEFAULT: hsl("card"), foreground: hsl("card-foreground") },
        primary: { DEFAULT: hsl("primary"), foreground: hsl("primary-foreground") },
        secondary: { DEFAULT: hsl("secondary"), foreground: hsl("foreground") },
        muted: { DEFAULT: hsl("muted"), foreground: hsl("muted-foreground") },
        accent: { DEFAULT: hsl("accent"), foreground: hsl("foreground") },
        border: hsl("border"),
        input: hsl("input"),
        ring: hsl("ring"),
        // domain semantic
        success: { DEFAULT: hsl("success"), foreground: hsl("success-foreground") },
        warning: { DEFAULT: hsl("warning"), foreground: hsl("warning-foreground") },
        destructive: { DEFAULT: hsl("destructive"), foreground: hsl("destructive-foreground") },
        info: hsl("info"),
        oee: { good: hsl("oee-good"), mid: hsl("oee-mid"), low: hsl("oee-low") },
        shift: { 1: hsl("shift-1"), 2: hsl("shift-2"), 3: hsl("shift-3") },
        chart: { 1: hsl("chart-1"), 2: hsl("chart-2"), 3: hsl("chart-3"), 4: hsl("chart-4"), 5: hsl("chart-5") },
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" },
      fontFamily: { sans: ["var(--font-sans)"], mono: ["var(--font-mono)"] },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
```

## Kullanım Örnekleri

```tsx
// Validasyon severity rozeti
<Badge className="bg-warning text-warning-foreground">Şüpheli</Badge>
<Badge className="bg-destructive text-destructive-foreground">Reddedildi</Badge>

// OEE değerine göre renk (helper)
const oeeColor = (oee: number) =>
  oee >= 85 ? "text-oee-good" : oee >= 60 ? "text-oee-mid" : "text-oee-low";

// Vardiya etiketi
<span className="text-shift-1">Sabah</span>
```

## Token Sözlüğü (anlamsal)

| Token | Anlam | Nerede |
|-------|-------|--------|
| `success` | Temiz/valid kayıt, başarılı gönderim | rozet, KPI, sync sonuç |
| `warning` | Şüpheli kayıt (uyar) | validation report |
| `destructive` | Hatalı kayıt (reddet), API 4xx/5xx | validation, sync hata |
| `info` | Bilgi / manuel düzeltildi | audit trail rozeti |
| `oee-{good,mid,low}` | OEE bandı (≥85 / 60–85 / <60) | KPI, grafik, tablo |
| `shift-{1,2,3}` | Vardiya (Sabah/Öğle/Gece) | grafik serileri, etiket |
| `chart-{1..5}` | Grafik serisi paleti | Recharts |

## Kurallar
- `text-red-500`, `bg-[#16a34a]` gibi hardcoded değer **kullanma**.
- Her zaman semantic token (`text-destructive`, `bg-success`).
- Yeni renk gerekirse önce token tanımla (`globals.css` + `tailwind.config.ts`), sonra kullan.
- Dark mode bedava gelir: `.dark` bloğunda CSS değişkenini override et, bileşeni değiştirme.
- Karşılık: case study "UI/UX" (%10) + "kullanıcıya hata bildirimleri ne kadar anlaşılır".
