# ADR 0003 — Validasyon Motoru Tasarımı

**Durum:** Kabul edildi · **Tarih:** 2026-06-17

## Bağlam
Validasyon değerlendirmenin %25'i (en yüksek). Çok sayıda hata tipi + gerekçe + düşük yanlış
pozitif gerekli. Kurallar test edilebilir, genişletilebilir, raporlanabilir olmalı.

## Karar
- **Kural = ayrı sınıf** (base `Rule`) + `check(record, context) -> Issue | None` metodu; bazı kurallar liste de döndürebilir. Her kural `rules/` altında ayrı dosyada.
- `engine.py` tüm kuralları kayda uygular → `Issue[]` üretir; kayıt status'u türetir.
- Her Issue: `rule_id, category, severity, fields, message, suggested_action`.
- **Severity/aksiyon ayrımı:** yüksek-güven → `reject`; sezgisel → `warn` (kullanıcı kararı).
- Kategoriler: missing, range, consistency, duplicate, format, domain (6).
- Katalog (kaynak doğruluk): [`validation-rules.md`](../domain/validation-rules.md).

## Alternatifler
| Alternatif | Neden hayır |
|------------|-------------|
| Tek dev `validate()` fonksiyonu | Test/bakım zor, kural ekleme kırılgan |
| Sadece Pydantic validator'ları | Satırlar-arası (duplicate) + istatistik (outlier) kuralları zor |
| Kural motoru kütüphanesi (great_expectations) | 2 gün için ağır; şeffaflık/açıklama zayıflar |

## Sonuçlar
- (+) Her kural ayrı birim test (pozitif + negatif/yanlış-pozitif önleme).
- (+) UI'dan kural eşik düzenleme (bonus) eklenebilir — eşikler config'te.
- (+) "Sistemik vs tekil" raporlama: aynı kural çok kayıtta → sistemik etiketi.
- (−) Satırlar-arası kurallar (duplicate) tüm batch'i görmeli → engine iki geçiş yapar
  (satır-içi + batch-düzeyi).
