# Validasyon Kural Kataloğu ( — %25)

> **Bu projenin en yüksek puanlı kısmı.** Her kural: kimlik, kategori, severity, önerilen aksiyon,
> koşul, **gerekçe** ve **örnek**. Yanlış pozitif puan kaybettirir → kurallar *confidence*
> seviyesine göre `reject` (yüksek güven) veya `warn/suspect` (kullanıcı kararına bırak) ayrılır.

## Tasarım Prensipleri
- **Severity:** `error` (veri kullanılamaz) · `warning` (şüpheli, incele) · `info` (kozmetik/normalize).
- **Aksiyon:** `reject` (hedef API'ye gitmez) · `warn` (işaretle, kullanıcı karar versin) · `fix`
  (otomatik normalize, audit'e yaz).
- **Confidence:** yüksek-güven kurallar otomatik reddeder; sezgisel olanlar yalnız işaretler.
- **Sistemik vs tekil:** bir hata tipi kayıtların >%X'inde görülüyorsa "sistemik" etiketlenir
  (kaynak/MES sorunu) ve raporda ayrı gruplanır (bonus: "sistemik sorun mu, tekil kayıt mı").
- **Tolerans:** float çapraz kontrollerde ±1.0 yüzde puan.

## Severity / Aksiyon Özet Matrisi
| Kategori | Tipik severity | Tipik aksiyon |
|----------|----------------|---------------|
| Eksik veri (zorunlu) | error | reject |
| Eksik veri (türetilebilir) | warning | fix (yeniden hesapla) |
| Aralık dışı | error | reject |
| Tutarsız ilişki | warning/error | warn / reject |
| Duplicate | error | reject (dedupe) |
| Format | info | fix (normalize) |
| Domain (imkânsız) | error | reject |

---

## A. Eksik / Boş Veri → (`category: missing`)

| ID | Alan(lar) | Koşul | Sev | Aksiyon | Gerekçe / Örnek |
|----|-----------|-------|-----|---------|-----------------|
| V-M01 | record_id | null/boş | error | reject | PK yok → kaydı izleyemeyiz. Örn: `record_id=""` |
| V-M02 | Tarih | null/boş | error | reject | Gün/vardiya kovasına atanamaz, API `production_date` zorunlu |
| V-M03 | Vardiya | null/boş | error | reject | API gönderimi vardiya bazında; eksikse gruplanamaz |
| V-M04 | İş İstasyon Adı | null/boş | error | reject | Temel boyut; istasyon kırılımı yapılamaz |
| V-M05 | Üretilen Miktar | null/boş | error | reject | Çekirdek metrik; OEE/üretim hesaplanamaz |
| V-M06 | OEE veya A/P/Q | biri null ama diğerleri dolu | warning | fix | Eksik bileşeni formülden yeniden hesapla (V-C02/03/04) |
| V-M07 | Stok Adı / İş Merkezi | null/boş | warning | warn | Opsiyonel boyut; reddetme, işaretle |

## B. Aralık Dışı Değerler → (`category: range`)

| ID | Alan | Koşul | Sev | Aksiyon | Gerekçe / Örnek |
|----|------|-------|-----|---------|-----------------|
| V-R01 | A | <0 veya >100 | error | reject | Yüzde 0–100 dışı imkânsız. Örn: `A=120` |
| V-R02 | Q | <0 veya >100 | error | reject | Kalite yüzdesi 0–100. Örn: `Q=-5` |
| V-R03 | OEE | <0 veya >100 | error | reject | OEE yüzde sınırı |
| V-R04 | P | <0 | error | reject | Negatif performans imkânsız |
| V-R05 | P | >100 (≤150) | warning | warn | İdealden hızlı olabilir ama şüpheli → incele |
| V-R06 | P | >150 | error | reject | Fiziksel olarak imkânsız hız |
| V-R07 | Üretilen Miktar | <0 | error | reject | Negatif üretim olamaz |
| V-R08 | Hatalı Üretilen Miktar | <0 | error | reject | Negatif fire olamaz |
| V-R09 | Süre alanları (4) | herhangi biri <0 | error | reject | Negatif süre imkânsız |
| V-R10 | Vardiya | ∉ {1,2,3} | error | reject | Tanımsız vardiya. Örn: `Vardiya=4` |

## C. Tutarsız İlişkiler → (`category: consistency`) — **en sofistike + en çok puan**

| ID | Alan(lar) | Koşul | Sev | Aksiyon | Gerekçe / Örnek |
|----|-----------|-------|-----|---------|-----------------|
| V-C01 | Hatalı, Üretilen | Hatalı > Üretilen | error | reject | Fire üretimden fazla olamaz. Örn: Üretilen=100, Hatalı=130 |
| V-C02 | OEE, A, P, Q | \|OEE − A·P·Q/10000\| > 1.0 | warning | warn | OEE bileşenleriyle uyumsuz → veri bütünlüğü |
| V-C03 | Q, Üretilen, Hatalı | \|Q − (Üretilen−Hatalı)/Üretilen·100\| > 1.0 | warning | warn | Kalite, fire ile tutarsız |
| V-C04 | A, Çalışma, Plansız Duruş | \|A − Çalışma/(Çalışma+Plansız)·100\| > 1.0 | warning | warn | Availability, sürelerle tutarsız |
| V-C05 | Duruş, Planlı, Plansız | \|Duruş − (Planlı+Plansız)\| > 1.0 | warning | warn | Toplam duruş = planlı + plansız olmalı |
| V-C06 | Üretilen, Çalışma | Üretilen>0 ama Çalışma=0 | error | reject | Çalışmadan üretim imkânsız |
| V-C07 | Çalışma, Üretilen, Duruş | Çalışma>0, Üretilen=0, Duruş=0 | warning | warn | Çalışıp hiç üretmemek + duruş yok → şüpheli |
| V-C08 | Q, Hatalı | Q=100 ama Hatalı>0 | error | reject | %100 kalite ama fire var → çelişki |
| V-C09 | A, Plansız Duruş | A=100 ama Plansız Duruş>0 | warning | warn | Tam kullanılırlık + plansız duruş çelişkisi |
| V-C10 | OEE, Üretilen | OEE>0 ama Üretilen=0 | warning | warn | Üretim yokken OEE>0 → sensör/log hatası |

## D. Duplicate Kayıtlar → (`category: duplicate`)

| ID | Anahtar | Koşul | Sev | Aksiyon | Gerekçe / Örnek |
|----|---------|-------|-----|---------|-----------------|
| V-D01 | tüm alanlar | satır birebir tekrar | error | reject | Aynı kayıt 2 kez (row_hash eşit) → dedupe |
| V-D02 | (Tarih,Vardiya,İstasyon,İş Emri) | aynı ama metrikler farklı | warning | warn | **Çelişen kayıt** — hangisi doğru? Kullanıcı seçsin |
| V-D03 | record_id | aynı record_id ≥2 satırda | error | reject | PK tekrarı |
| V-D04 | dosya (file_hash) | aynı CSV tekrar yüklenmiş | warning | warn | Import düzeyinde duplicate (5.1 gereği) |

## E. Format Tutarsızlıkları → (`category: format`)

| ID | Alan | Koşul | Sev | Aksiyon | Gerekçe / Örnek |
|----|------|-------|-----|---------|-----------------|
| V-F01 | Tarih | farklı format (DD.MM.YYYY / YYYY-MM-DD / DD/MM/YYYY) | info | fix | Tek formata (ISO) normalize |
| V-F02 | float alanlar | ondalık ayraç virgül (`87,3`) | info | fix | Nokta'ya normalize |
| V-F03 | yüzde alanlar | 0–1 ölçeğinde (`0.87`) | warning | fix | 0–100'e ölçekle (tespit: tüm A/P/Q ≤1 ise) |
| V-F04 | İş Emri No | `^302\d{7}$` deseni tutmuyor | warning | warn | Beklenen iş emri formatı dışı |
| V-F05 | string alanlar | baş/son boşluk, tutarsız case | info | fix | Trim + normalize |
| V-F06 | İş İstasyon Adı | `IMM-####-#` deseni dışı | info | warn | Beklenen makine kodu formatı dışı |

## F. Domain Mantığı / Fiziksel İmknsız → (`category: domain`)

| ID | Alan(lar) | Koşul | Sev | Aksiyon | Gerekçe / Örnek |
|----|-----------|-------|-----|---------|-----------------|
| V-X01 | Tarih | gelecek tarih (> bugün) | error | reject | API gelecek tarihi kabul etmez; üretim geleceğe olmaz |
| V-X02 | Tarih | rapor penceresi dışı (5–25 Kas 2025 dışı) | warning | warn | Beklenen aralık dışı → incele |
| V-X03 | Çalışma+Duruş | toplam > 1440 dk (1 gün) | error | reject | Bir günde 1440 dk'dan fazla olamaz |
| V-X04 | Plansız Duruş | > (Çalışma+Plansız) | error | reject | Duruş, toplam mevcut süreden fazla olamaz |
| V-X05 | Üretilen Miktar | makul kapasitenin çok üstü (istatistiksel outlier) | warning | warn | Outlier → hata mı normal mi? Sınıflandır, reddetme |
| V-X06 | OEE | =0 ama tam üretim+çalışma var | warning | warn | Sıfır OEE + dolu üretim → ölçüm hatası |

---

## Outlier Politikası (case FAQ: "doğal outlier'lar hata mı?")
Outlier'lar **otomatik reddedilmez**. İstatistiksel yöntemle (IQR / z-score) tespit edilir,
`warning` olarak işaretlenir ve raporda "incele" der. Kullanıcı normal mi anomali mi karar verir.
Bu, "yanlış pozitif puan kaybettirir" uyarısına uyumu sağlar.

## Validation Report Çıktısı (her şüpheli kayıt için)
```json
{
  "record_id": 1487,
  "issues": [
    { "rule_id": "V-C01", "category": "consistency", "severity": "error",
      "fields": ["Hatalı Üretilen Miktar", "Üretilen Miktar"],
      "message": "Fire (130) üretimden (100) fazla.", "suggested_action": "reject" }
  ],
  "record_status": "rejected"
}
```

## Kural Motoru Yerleşimi
`backend/app/features/validation/`:
- `engine.py` — tüm kuralları kayıt üzerinde çalıştırır, issue listesi üretir.
- `rules/` — her kategori ayrı dosya (`missing.py`, `range_.py`, `consistency.py`, `duplicate.py`, `format_.py`, `domain.py`); her kural `Rule` tabanlı bir sınıf, `check(record, ctx) -> Issue | None` (bazıları liste de döndürür), birim test'li.
- `report.py` — issue'ları sınıflandırır, import özeti + indirilebilir rapor (bonus) üretir.

## Test Stratejisi
Her kural için pozitif (yakalamalı) + negatif (yakalamamalı = yanlış pozitif önleme) test.
 `backend/tests/test_validation.py` (parametrize ile kural başına pozitif+negatif vakalar + 2 engine end-to-end testi). (Kod kalitesi %15 + bonus "validasyon birim testleri".)
