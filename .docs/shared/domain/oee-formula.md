# OEE Formülü (Referans)

OEE (Overall Equipment Effectiveness) endüstri standardı verimlilik metriği.

## Formül
```
OEE = A × P × Q / 10000        (yüzde formatında, çünkü A,P,Q yüzde)
```

| Bileşen | Tanım | Formül |
|---------|-------|--------|
| **A** (Availability/Kullanılırlık) | Makinenin çalışmaya hazır olma oranı | `Çalışma Süresi / (Çalışma Süresi + Plansız Duruş Süresi) × 100` |
| **P** (Performance/Performans) | İdeal hıza karşı gerçekleşen hız | ideal_hız'a göre (kaynakta verili) |
| **Q** (Quality/Kalite) | Sağlam ürün oranı | `(Üretilen − Hatalı) / Üretilen × 100` |

## Çalışılmış Örnek
```
A = 90, P = 95, Q = 98
OEE = 90 × 95 × 98 / 10000 = 83.79 %
```

## World-Class Referans (yorum için)
| OEE | Değerlendirme | Token |
|-----|---------------|-------|
| ≥ 85% | Dünya standardı | `oee-good` |
| 60–85% | Tipik | `oee-mid` |
| < 60% | İyileştirme gerekli | `oee-low` |

## Validasyon İçin Önemi (kritik)
Kaynak veride A, P, Q, OEE **zaten dolu** geliyor. Ama gerçek MES verisi tutarsız olabilir:

1. **OEE çapraz kontrolü:** `OEE ≟ A·P·Q/10000` (tolerans ±1.0 puan). Tutmazsa → veri bütünlüğü
   sorunu (V-C02).
2. **Q çapraz kontrolü:** `Q ≟ (Üretilen−Hatalı)/Üretilen×100` (V-C03).
3. **A çapraz kontrolü:** `A ≟ Çalışma/(Çalışma+Plansız Duruş)×100` (V-C04).
4. **Yeniden hesap:** Tutarsızlıkta hangisinin "doğru" olduğuna kullanıcı karar verir; sistem
   `oee_recomputed` alanında bizim hesabımızı saklar ve farkı gösterir.

> Bu çapraz kontroller validasyon "tutarsız ilişkiler" kategorisinin (V-C\*) çekirdeğidir ve
> case study'nin en çok puan veren kısmıdır. Bkz.
> [`validation-rules.md`](validation-rules.md).

## Tolerans Politikası
Float karşılaştırmalarında **±1.0 yüzde puan** tolerans (yuvarlama/MES hassasiyeti için).
Bu eşik `app/core/config.py` içinde `validation_tolerance_pct` ayarıdır (varsayılan 1.0);
RuleContext üzerinden consistency kurallarına enjekte edilir ve `.env` ile değiştirilebilir.
