# Proje Belleği (curated)

> Kısa ve güncel tut. Önemli kararlar, mevcut durum, öğrenilenler.

## Mevcut Durum
- Çekirdek feature fazları uygulandı: backend (ingestion, validation, analytics, records, sync) + frontend (import, dashboard, records, validation, sync) feature kodu yazıldı; 38 backend testi geçiyor.
- Backend feature'ları gerçek `api.py`/`service.py`/`engine.py` ile hazır; 6 tablolu DB şeması ve 43 kurallı (6 kategori) validasyon motoru mevcut.

## Önemli Kararlar (özet — detay: `.docs/shared/decisions/`)
- Stack: Next.js + shadcn/ui + FastAPI + SQLite.
- Hedef API gönderimi (gün, vardiya) bazında agrege; idempotent + retry.
- Validasyon: saf-fonksiyon kural motoru; reject (yüksek güven) vs warn (sezgisel) ayrımı.
- AI bağlam: `AGENTS.md` canonical → `CLAUDE.md` kopya (`make ai-sync`). Kapsam: MiniMax + Claude.
- Feature izolasyonu ESLint (`boundaries`) ile zorunlu; ortak kod `shared`'a.

## Öğrenilenler / Dikkat
- Türkçe karakter (`â`) ve ok (`→`) içeren toplu sed/perl'de `-CSD` kodlaması güvenilmez;
  bayt-modu + codepoint (`\x{...}`) kullan.
- `bfs` (bu ortamdaki find) çoklu `{}` desteklemez; `xargs -0` tercih et.
- zsh unquoted `$(...)` kelime-bölmez; dosya listelerini `find -print0 | xargs -0` ile geçir.
