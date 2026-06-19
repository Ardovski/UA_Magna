"""Records API router — sunucu-taraflı sayfalı liste, CSV export ve kayıt detay endpoint'leri."""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.features.records.export import csv_filename, rows_to_csv_lines
from app.features.records.schemas import DateRange, OeeRange, PaginatedRecords, RecordFilter
from app.features.records.service import (
    distinct_values,
    get_record,
    list_records,
    stream_records,
)

router = APIRouter()


def _build_filter(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
) -> RecordFilter:
    """Query string filtre parametrelerini ortak `RecordFilter` şemasına derler
    (liste ve export ortak kullanır)."""
    return RecordFilter(
        # Tarih/OEE alt-aralıkları yalnız ilgili parametreler verildiğinde kurulur.
        prod_date_range=DateRange(start=start, end=end) if (start or end) else None,
        shift=shift or [],
        station_name=station_name or [],
        stock_name=stock_name,
        oee_range=OeeRange(min=oee_min, max=oee_max)
        if (oee_min is not None or oee_max is not None)
        else None,
        validation_status=validation_status or [],
        has_issues=has_issues,
    )


@router.get("/list", response_model=PaginatedRecords)
def list_(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    sort: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedRecords:
    """Filtre + sıralama + sayfalama ile kayıt listesi; toplam ve sayfa sayısıyla birlikte döner."""
    flt = _build_filter(
        start=start,
        end=end,
        shift=shift,
        station_name=station_name,
        stock_name=stock_name,
        oee_min=oee_min,
        oee_max=oee_max,
        validation_status=validation_status,
        has_issues=has_issues,
    )
    items, total = list_records(db, flt, page=page, size=size, sort=sort)
    # Toplam sayfa = tavan(total / size); size 0 ise (teorik) 0.
    total_pages = (total + size - 1) // size if size else 0
    return PaginatedRecords(items=items, page=page, size=size, total=total, total_pages=total_pages)


@router.get("/export")
def export(
    start: Annotated[dt.date | None, Query()] = None,
    end: Annotated[dt.date | None, Query()] = None,
    shift: Annotated[list[int] | None, Query()] = None,
    station_name: Annotated[list[str] | None, Query()] = None,
    stock_name: Annotated[str | None, Query()] = None,
    oee_min: Annotated[float | None, Query()] = None,
    oee_max: Annotated[float | None, Query()] = None,
    validation_status: Annotated[list[str] | None, Query()] = None,
    has_issues: Annotated[bool | None, Query()] = None,
    sort: str | None = None,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Aynı filtre/sıralamayı uygulayan kayıtları CSV olarak akıtarak indirir
    (sayfalama yok; tüm sonuç kümesi)."""
    flt = _build_filter(
        start=start,
        end=end,
        shift=shift,
        station_name=station_name,
        stock_name=stock_name,
        oee_min=oee_min,
        oee_max=oee_max,
        validation_status=validation_status,
        has_issues=has_issues,
    )

    def iter_csv() -> AsyncIterator[bytes]:
        # UTF-8 BOM: Excel'in Türkçe karakterleri doğru kodlama ile açması için ilk yazılan bayttır.
        yield b"\xef\xbb\xbf"
        # Kayıtlar yield_per ile akıtılır; satır satır CSV'ye çevrilip byte'a kodlanır
        # (tüm seti belleğe almadan).
        for chunk in rows_to_csv_lines(stream_records(db, flt, sort=sort)):
            yield chunk.encode("utf-8")

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            # Tarayıcıya dosya indirmesi (attachment) ve zaman damgalı dosya adı verir;
            # cevap önbelleğe alınmaz.
            "Content-Disposition": f'attachment; filename="{csv_filename()}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/distinct/{column}")
def distinct(
    column: str,
    db: Session = Depends(get_db),
) -> list[str]:
    """Verilen kolon için ayrık (distinct) değer listesi; filtre açılır menülerini besler."""
    return distinct_values(db, column)


@router.get("/{record_id}")
def detail(
    record_id: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Tek kaydın detayını (ilişkili validasyon sorunları dahil) döner; yoksa 404."""
    rec = get_record(db, record_id)
    if rec is None:
        raise NotFoundError(f"Record {record_id} bulunamadı.")
    return rec.model_dump()
