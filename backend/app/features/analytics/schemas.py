"""Analytics Pydantic şemaları."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class KpiCards(BaseModel):
    """Dashboard üst KPI kartları: ortalama OEE, toplam üretim/fire/duruş ve statü kırılımı."""

    avg_oee: float | None = None
    total_production: int = 0
    total_scrap: int = 0
    total_down_time_minutes: float = 0.0
    record_count: int = 0
    valid_count: int = 0
    suspect_count: int = 0
    rejected_count: int = 0


class OeeTrendPoint(BaseModel):
    """OEE trend grafiğinde tek bir gün noktası (tarih + o günün ortalama OEE'si)."""

    prod_date: dt.date
    avg_oee: float | None = None
    total_production: int = 0
    record_count: int = 0


class ShiftComparisonRow(BaseModel):
    """Vardiya karşılaştırma tablosunda tek bir vardiyanın agregat satırı."""

    shift: int
    avg_oee: float | None = None
    total_production: int = 0
    total_scrap: int = 0
    record_count: int = 0


class StationRankingRow(BaseModel):
    """İstasyon sıralamasında tek bir istasyonun agregat satırı (OEE'ye göre sıralanır)."""

    station_name: str
    avg_oee: float | None = None
    total_production: int = 0
    record_count: int = 0


class QualityDistributionBucket(BaseModel):
    """Kalite (Q) histogramında tek bir aralık (bucket): sınırlar, kayıt sayısı ve fire toplamı."""

    bucket_label: str
    bucket_start: float
    bucket_end: float
    record_count: int
    total_scrap: int = 0


class RecentRecordOut(BaseModel):
    """Dashboard "son kayıtlar" tablosunun özet satırı (tam kayıt değil)."""

    id: int
    prod_date: dt.date | None = None
    shift: int | None = None
    station_name: str | None = None
    stock_name: str | None = None
    oee: float | None = None
    produced_qty: int | None = None
    scrap_qty: int | None = None
    status: str
    created_at: dt.datetime | None = None


class TopStationOut(BaseModel):
    """Dashboard "en iyi istasyonlar" tablo satırı (batch bazlı agregat)."""

    station_name: str
    avg_oee: float | None = None
    total_production: int = 0
    total_scrap: int = 0
    record_count: int = 0


class ProblemShiftOut(BaseModel):
    """Dashboard "sorunlu vardiyalar" tablo satırı: düşük OEE veya red edilmiş kayıt içeren grup."""

    prod_date: dt.date | None = None
    shift: int
    station_name: str | None = None
    avg_oee: float | None = None
    rejected_count: int = 0
    total_production: int = 0
    record_count: int = 0
