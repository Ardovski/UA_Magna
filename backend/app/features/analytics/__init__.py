"""Analytics feature — OEE hesaplamaları ve dashboard agregasyonları.

5 filtre-aware sorgu sağlar:
  - kpis                : toplam üretim, fire, duruş, ortalama OEE (tüm kayıt vs valid+fixed).
  - oee_trend           : günlük ortalama OEE serisi (varsayılan son 21 gün).
  - shift_comparison    : vardiya bazlı performans karşılaştırma.
  - station_ranking     : istasyon bazlı OEE sıralaması (top N).
  - quality_distribution: Q histogramı (10'ar yüzdelik dilim).
"""
