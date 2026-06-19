import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Üretim Performans Takip",
  description: "MAGNA case study — OEE & üretim kalite takip uygulaması",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Not: `next/font/google` (Inter, JetBrains_Mono) build-time'da Google Fonts'tan
  // font dosyalarını indirip indirip gömüyor. İnternet yok / yavaş / bloklu
  // ortamlarda build sırasında 30s timeout cascade veriyor ve sayfa fallback
  // font'a düşüyor. Sistem font stack'i (`ui-sans-serif`/`ui-monospace` Tailwind
  // defaults) yeterli görsel kaliteyi veriyor + sıfır dış bağımlılık.
  return (
    <html lang="tr" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
