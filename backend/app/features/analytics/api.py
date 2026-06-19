"""Analytics API router — KPI + 4 grafik + 3 dashboard tablo endpoint'i."""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.analytics.service import (
    kpis,
    oee_trend,
    problem_shifts,
    quality_distribution,
    recent_records,
    shift_comparison,
    station_ranking,
    top_stations,
)
from app.features.records.schemas import DateRange, OeeRange, RecordFilter
from app.features.records.service import distinct_values

router = APIRouter()


def _parse_filters(
    start: dt.date | None,
    end: dt.date | None,
    shift: list[int] | None,
    station_name: list[str] | None,
    stock_name: str | None,
    oee_min: float | None,
    oee_max: float | None,
    validation_status: list[str] | None,
    has_issues: bool | None,
) -> RecordFilter:
    """Query string parametrelerini tek bir `RecordFilter` nesnesine derler.

    Tüm analytics endpoint'leri aynı zengin filtre setini paylaşır; bu yardımcı
    dağınık query parametrelerini records modülündeki ortak filtre şemasına
    dönüştürür. Boş/None değerler ilgili alt-şemaları (tarih/OEE aralığı) hiç
    kurmadan atlar, böylece filtre uygulanmamış sayılır.
    """
    return RecordFilter(
        # Tarih aralığı yalnız start veya end verilmişse kurulur; aksi halde None.
        prod_date_range=DateRange(start=start, end=end) if (start or end) else None,
        shift=shift or [],
        station_name=station_name or [],
        stock_name=stock_name,
        # OEE aralığı yalnız min veya max verilmişse kurulur.
        oee_range=OeeRange(min=oee_min, max=oee_max)
        if (oee_min is not None or oee_max is not None)
        else None,
        validation_status=validation_status or [],
        has_issues=has_issues,
    )


@router.get("/kpis")
def kpis_endpoint(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Dashboard üst KPI kartları: ortalama OEE, toplam üretim/fire/duruş ve statü sayıları."""
    flt = _parse_filters(
        start, end, shift, station_name, stock_name, oee_min, oee_max, validation_status, has_issues
    )
    return kpis(db, flt)


@router.get("/oee-trend")
def oee_trend_endpoint(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    days: int = Query(21, ge=1, le=90),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Günlük OEE trend serisi: son `days` gün için tarih bazında ortalama OEE."""
    flt = _parse_filters(
        start, end, shift, station_name, stock_name, oee_min, oee_max, validation_status, has_issues
    )
    return oee_trend(db, flt, days=days)


@router.get("/shift-comparison")
def shift_comparison_endpoint(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Vardiya karşılaştırması: her vardiya için ortalama OEE, üretim ve fire."""
    flt = _parse_filters(
        start, end, shift, station_name, stock_name, oee_min, oee_max, validation_status, has_issues
    )
    return shift_comparison(db, flt)


@router.get("/station-ranking")
def station_ranking_endpoint(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """İstasyon sıralaması: ortalama OEE'ye göre en iyi `limit` istasyon."""
    flt = _parse_filters(
        start, end, shift, station_name, stock_name, oee_min, oee_max, validation_status, has_issues
    )
    return station_ranking(db, flt, limit=limit)


@router.get("/quality-distribution")
def quality_distribution_endpoint(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Kalite dağılımı: kayıtları 10'arlık kalite (Q) aralıklarına (bucket) ayırır."""
    flt = _parse_filters(
        start, end, shift, station_name, stock_name, oee_min, oee_max, validation_status, has_issues
    )
    return quality_distribution(db, flt)


@router.get("/recent-records")
def recent_records_endpoint(
    batch_id: Annotated[int | None, Query()] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Dashboard "son kayıtlar" tablosu; isteğe bağlı olarak tek bir import batch'ine daraltılır."""
    return recent_records(db, batch_id=batch_id, limit=limit)


@router.get("/top-stations")
def top_stations_endpoint(
    batch_id: Annotated[int | None, Query()] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Dashboard "en iyi istasyonlar" tablosu (batch bazlı, OEE'ye göre sıralı)."""
    return top_stations(db, batch_id=batch_id, limit=limit)


@router.get("/problem-shifts")
def problem_shifts_endpoint(
    batch_id: Annotated[int | None, Query()] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Dashboard "sorunlu vardiyalar" tablosu: düşük OEE veya red edilmiş kayıt
    içeren (tarih, vardiya, istasyon) grupları."""
    return problem_shifts(db, batch_id=batch_id, limit=limit)


@router.get("/filter-options")
def filter_options(db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Filtre açılır menüleri için ayrık (distinct) değer listelerini döner."""
    return {
        "stations": distinct_values(db, "station_name"),
        "stock_names": distinct_values(db, "stock_name"),
        "work_centers": distinct_values(db, "work_center_name"),
    }
