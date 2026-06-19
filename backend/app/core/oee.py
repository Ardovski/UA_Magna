"""OEE yeniden hesaplama — MES'in hazır `OEE` kolonuna güvenmeden, ham
bileşenlerden standart formülle hesaplar.

    OEE = A × P × Q / 10000   (yüzde)
    A (Availability) = Çalışma / (Çalışma + Plansız Duruş)        ← süre kolonlarından
    P (Performance)  = ideal hıza karşı gerçekleşen hız            ← kolondan (verilen)
    Q (Quality)      = (Üretilen − Hatalı) / Üretilen              ← miktar kolonlarından

Neden yeniden hesap? Ham `OEE`/`P` kolonlarında fiziksel olarak imkânsız
değerler var (787 kayıtta P>100 → OEE>100). Bu garbage ortalamayı şişirir.
Bileşenler [0, 100] aralığına clamp'lenir (OEE konvansiyonu: performans %100'ü
aşamaz). Detay: `.docs/shared/domain/`.
"""

from __future__ import annotations


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Değeri [lo, hi] aralığına sıkıştırır (OEE bileşenlerini %0-100'e sabitlemek için)."""
    return max(lo, min(v, hi))


def recompute_oee(
    *,
    run_time: float | None,
    unplanned_down: float | None,
    performance: float | None,
    produced_qty: int | None,
    scrap_qty: int | None,
) -> float | None:
    """Ham bileşenlerden OEE (yüzde) döndürür.

    Kurallar:
    - Çalışma + Plansız Duruş = 0 (makine hiç aktif değil) → ``None`` (ortalama
      dışı; planlanmamış/boş kayıt).
    - Üretim = 0 ama makine aktif → Q = 0 → OEE = 0 (gerçek verimlilik kaybı).
    - Performans yoksa hesaplanamaz → ``None``.
    - A, P, Q her biri [0, 100] aralığına clamp'lenir.
    """
    # Performans veya süre bilgisi eksikse OEE anlamlı hesaplanamaz.
    if performance is None or run_time is None or unplanned_down is None:
        return None
    # Availability paydası: toplam aktif süre (çalışma + plansız duruş).
    denom = float(run_time) + float(unplanned_down)
    if denom <= 0.0:
        return None

    # A: kullanılabilirlik yüzdesi (çalışma süresinin toplam aktif süreye oranı).
    a = _clamp(float(run_time) / denom * 100.0)
    # P: ham performans kolonu; konvansiyon gereği %100'ü aşamaz, clamp'lenir.
    p = _clamp(float(performance))

    produced = int(produced_qty) if produced_qty is not None else 0
    scrap = int(scrap_qty) if scrap_qty is not None else 0
    # Q: kalite yüzdesi = (üretilen - hatalı) / üretilen; üretim yoksa 0 (gerçek kayıp).
    q = 0.0 if produced <= 0 else _clamp((produced - scrap) / produced * 100.0)

    # Standart OEE: A·P·Q üç yüzdenin çarpımı /10000 ile tek yüzdeye normalize edilir.
    return a * p * q / 10000.0
