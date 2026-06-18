# Validasyon Motoru (Implementasyon)

Bu doküman motorun **nasıl** çalıştığını anlatır. **Hangi** kuralların uygulandığı ayrı bir
spesifikasyondur: [`../shared/domain/validation-rules.md`](../shared/domain/validation-rules.md).

## Yerleşim
```
backend/app/features/validation/
├── engine.py        # kuralları kayıtlara uygular, Issue listesi üretir
├── report.py        # issue'ları sınıflandırır, özet + indirilebilir rapor (bonus)
└── rules/
    ├── __init__.py  # kural registry'si
    ├── base.py
    ├── missing.py
    ├── range_.py
    ├── consistency.py
    ├── duplicate.py
    ├── format_.py
    └── domain.py
```

## Çalışma Modeli
İki geçiş:
1. **Satır-içi kurallar** — her kayıt tek başına değerlendirilir (eksik, aralık, tutarsızlık,
   format, domain).
2. **Batch kuralları** — tüm yükleme görünür olmalı (duplicate tespiti, istatistiksel outlier).

Her kural saf bir fonksiyondur:
```python
def rule(record, ctx) -> Issue | None: ...
```
Yan etkisi yoktur; yalnız bir `Issue` veya `None` döndürür. Eşikler (`OEE_TOLERANCE` vb.)
sabit/`config`'te tutulur — kodda magic number yok.

## Issue ve Kayıt Durumu
- `Issue`: `rule_id, category, severity, fields, message, suggested_action`.
- Kayıt durumu issue'lardan türetilir:
  - durum yalnız issue **severity**'sinden türetilir (`suggested_action`'dan değil)
  - en az bir `error` → `rejected`
  - error yoksa en az bir `warning` → `suspect`
  - aksi halde → `valid` (yalnız `info` severity'li issue'lar durumu `valid` bırakır)
- Issue'lar kalıcı olarak **YAZILMAZ** — her istekte `run_validation` ile bellekte yeniden
  hesaplanır (`validation_issues` tablosu şemada var ama hiç doldurulmaz). Yalnız türetilen kayıt
  durumu `production_records.status`'a yazılır; manuel düzeltmeler `record_edits`'e (kalıcı) yazılır.

## Sistemik vs Tekil (bonus)
Bir kural yüklemenin önemli bir oranında tetikleniyorsa "sistemik" etiketlenir (kaynak/MES
sorunu) ve raporda ayrı gruplanır.

## Test
`backend/tests/test_validation.py` — `parametrize` ile kurallar için pozitif (tetiklenir) ve
negatif (temiz/sınır kayıt tetiklenmez) satırlar + 2 uçtan uca motor testi (durum atama ve batch
V-D02/V-X05). Yanlış pozitif önleme bu negatif testlerle güvenceye alınır.

## İlgili
- Kural kataloğu (spec): [`../shared/domain/validation-rules.md`](../shared/domain/validation-rules.md)
- Karar kaydı: [`../shared/decisions/0003-validation-engine.md`](../shared/decisions/0003-validation-engine.md)
- Skill: `.claude/skills/add-validation-rule/`
