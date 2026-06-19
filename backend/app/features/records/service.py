"""Records service — filtre query builder + paginated list + detail."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import models
from app.features.records.schemas import (
    DateRange,
    OeeRange,
    RecordDetailOut,
    RecordFilter,
    RecordOut,
)

# İzin verilen sıralama alanları: dış API'den gelen sort string'i yalnız bu
# whitelist'teki kolonlara eşlenir (rastgele/güvensiz kolon sıralaması engellenir).
_SORT_FIELD_MAP: dict[str, Any] = {
    "id": models.ProductionRecord.id,
    "prod_date": models.ProductionRecord.prod_date,
    "shift": models.ProductionRecord.shift,
    "station_name": models.ProductionRecord.station_name,
    "stock_name": models.ProductionRecord.stock_name,
    "oee": models.ProductionRecord.oee,
    "produced_qty": models.ProductionRecord.produced_qty,
    "validation_status": models.ProductionRecord.status,
    "created_at": models.ProductionRecord.created_at,
}

_ALLOWED_SORT_FIELDS: frozenset[str] = frozenset(_SORT_FIELD_MAP.keys())
_DEFAULT_SORT: tuple[Any, bool] = (models.ProductionRecord.prod_date, True)


def _apply_filter(
    stmt: Any,
    flt: RecordFilter,
    issue_subq: Any | None = None,
) -> Any:
    """`RecordFilter` alanlarını SQL WHERE koşullarına çevirip statement'a ekler
    (records ve analytics ortak kullanır).

    Verilmeyen (None/boş) filtreler atlanır; verilen tüm koşullar AND'lenir.
    """
    conds: list[Any] = []

    rng: DateRange | None = flt.prod_date_range
    if rng is not None:
        if rng.start is not None:
            conds.append(models.ProductionRecord.prod_date >= rng.start)
        if rng.end is not None:
            conds.append(models.ProductionRecord.prod_date <= rng.end)

    if flt.shift:
        conds.append(models.ProductionRecord.shift.in_(flt.shift))

    if flt.station_name:
        conds.append(models.ProductionRecord.station_name.in_(flt.station_name))

    if flt.stock_name:
        # Stok adı: büyük/küçük harf duyarsız kısmi eşleşme (substring arama).
        conds.append(models.ProductionRecord.stock_name.ilike(f"%{flt.stock_name}%"))

    oee: OeeRange | None = flt.oee_range
    if oee is not None:
        if oee.min is not None:
            conds.append(models.ProductionRecord.oee >= oee.min)
        if oee.max is not None:
            conds.append(models.ProductionRecord.oee <= oee.max)

    if flt.validation_status:
        conds.append(models.ProductionRecord.status.in_(flt.validation_status))

    # has_issues: True -> sorunlu kayıtlar; False -> sorunsuz (0 veya hiç issue satırı = NULL).
    if flt.has_issues is True and issue_subq is not None:
        conds.append(issue_subq.c.issue_count > 0)
    elif flt.has_issues is False and issue_subq is not None:
        conds.append(or_(issue_subq.c.issue_count == 0, issue_subq.c.issue_count.is_(None)))

    if conds:
        stmt = stmt.where(and_(*conds))
    return stmt


def _sort_clause(sort: str | None) -> tuple[Any, ...]:
    if not sort:
        return (_DEFAULT_SORT[0].desc(),) if _DEFAULT_SORT[1] else (_DEFAULT_SORT[0].asc(),)
    parts = sort.split(":")
    field = parts[0]
    direction = parts[1].lower() if len(parts) > 1 else "asc"
    if field not in _ALLOWED_SORT_FIELDS:
        col, desc = _DEFAULT_SORT
    else:
        col = _SORT_FIELD_MAP[field]
        desc = direction == "desc"
    return (col.desc() if desc else col.asc(), models.ProductionRecord.id.desc())


def _to_record_out(row: Any) -> RecordOut:
    return RecordOut(
        id=row.id,
        record_id_src=row.record_id_src,
        import_batch_id=row.import_batch_id,
        prod_date=row.prod_date,
        work_order_no=row.work_order_no,
        work_center_no=row.work_center_no,
        work_center_name=row.work_center_name,
        station_name=row.station_name,
        stock_name=row.stock_name,
        shift=row.shift,
        availability=row.availability,
        performance=row.performance,
        quality=row.quality,
        oee=row.oee,
        run_time=row.run_time,
        down_time=row.down_time,
        planned_down=row.planned_down,
        unplanned_down=row.unplanned_down,
        produced_qty=row.produced_qty,
        scrap_qty=row.scrap_qty,
        oee_recomputed=row.oee_recomputed,
        validation_status=row.status,
        issue_count=int(getattr(row, "issue_count", 0) or 0),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _build_issue_subquery() -> Any:
    return (
        select(
            models.ValidationIssue.record_id.label("rid"),
            func.count(models.ValidationIssue.id).label("issue_count"),
        )
        .group_by(models.ValidationIssue.record_id)
        .subquery()
    )


def list_records(
    db: Session,
    flt: RecordFilter,
    page: int = 1,
    size: int = 50,
    sort: str | None = None,
) -> tuple[list[RecordOut], int]:
    issue_subq = _build_issue_subquery()
    count_stmt = select(func.count(models.ProductionRecord.id))
    count_stmt = _apply_filter(count_stmt, flt, issue_subq=issue_subq)
    total: int = int(db.execute(count_stmt).scalar_one() or 0)

    base = select(
        models.ProductionRecord,
        func.coalesce(issue_subq.c.issue_count, 0).label("issue_count"),
    ).outerjoin(
        issue_subq,
        issue_subq.c.rid == models.ProductionRecord.id,
    )
    base = _apply_filter(base, flt, issue_subq=issue_subq)
    order = _sort_clause(sort)
    base = base.order_by(*order)
    page = max(page, 1)
    size = max(min(size, 500), 1)
    base = base.offset((page - 1) * size).limit(size)

    rows = db.execute(base).all()
    items = [_to_record_out(r[0]).model_copy(update={"issue_count": int(r[1] or 0)}) for r in rows]
    return items, total


def get_record(db: Session, record_id: int) -> RecordDetailOut | None:
    issue_subq = _build_issue_subquery()
    stmt = (
        select(
            models.ProductionRecord,
            func.coalesce(issue_subq.c.issue_count, 0).label("issue_count"),
        )
        .outerjoin(
            issue_subq,
            issue_subq.c.rid == models.ProductionRecord.id,
        )
        .where(models.ProductionRecord.id == record_id)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    base = _to_record_out(row[0]).model_copy(update={"issue_count": int(row[1] or 0)})
    issues = (
        db.execute(
            select(models.ValidationIssue)
            .where(models.ValidationIssue.record_id == record_id)
            .order_by(models.ValidationIssue.id.asc())
        )
        .scalars()
        .all()
    )
    from app.features.records.schemas import IssueOut

    issue_outs = [
        IssueOut(
            id=i.id,
            rule_id=i.rule_id,
            category=i.category,
            severity=i.severity,
            fields=i.field_names,
            message=i.message,
            suggested_action=i.suggested_action,
            status=i.status,
            detected_at=i.detected_at,
            fixed_at=i.fixed_at,
        )
        for i in issues
    ]
    return RecordDetailOut(**base.model_dump(), issues=issue_outs)


def stream_records(
    db: Session,
    flt: RecordFilter,
    sort: str | None = None,
    batch_size: int = 500,
) -> Any:
    issue_subq = _build_issue_subquery()
    base = select(
        models.ProductionRecord,
        func.coalesce(issue_subq.c.issue_count, 0).label("issue_count"),
    ).outerjoin(
        issue_subq,
        issue_subq.c.rid == models.ProductionRecord.id,
    )
    base = _apply_filter(base, flt, issue_subq=issue_subq)
    base = base.order_by(*_sort_clause(sort))
    return db.execute(base).yield_per(batch_size)


def distinct_values(
    db: Session,
    column: str,
    limit: int = 200,
) -> list[str]:
    col = getattr(models.ProductionRecord, column, None)
    if col is None:
        return []
    stmt = select(col).where(col.isnot(None)).distinct().order_by(col.asc()).limit(limit)
    return [str(v) for v in db.execute(stmt).scalars().all() if v is not None]
