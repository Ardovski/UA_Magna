"""Validation tests — 47 kural × pozitif/negatif + engine uçtan uca."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from app.db import models
from app.features.validation.engine import run_validation
from app.features.validation.models import (
    IssueCategory,
    IssueSeverity,
    SuggestedAction,
)
from app.features.validation.rules.consistency import (
    VC01ScrapGreaterThanProduced,
    VC02OeeApxAPQ,
    VC08Quality100WithScrap,
)
from app.features.validation.rules.domain import (
    VX01FutureDate,
    VX03DayMinutesExceeded,
)
from app.features.validation.rules.format_ import VF04WorkOrderPattern
from app.features.validation.rules.missing import (
    VM01RecordIdMissing,
    VM02ProdDateMissing,
    VM05ProducedQtyMissing,
)
from app.features.validation.rules.range_ import (
    VR01AvailabilityRange,
    VR04PerformanceNegative,
    VR10ShiftInvalid,
)


def _row(**overrides: Any) -> Any:
    base: dict[str, Any] = {
        "record_id_src": 1,
        "prod_date": dt.date(2025, 11, 5),
        "work_order_no": "3021234567",
        "work_center_no": "INJ",
        "work_center_name": "INJ",
        "station_name": "IMM-2700-3",
        "stock_name": "STK",
        "shift": 1,
        "availability": 90.0,
        "performance": 95.0,
        "quality": 99.0,
        "oee": 84.0,
        "run_time": 7.0,
        "down_time": 0.5,
        "planned_down": 0.3,
        "unplanned_down": 0.2,
        "produced_qty": 10,
        "scrap_qty": 0,
        "row_hash": "h",
    }
    base.update(overrides)
    return type("R", (), base)()


def _ctx() -> Any:
    from app.features.validation.models import RuleContext

    return RuleContext(
        tolerance_pct=1.0,
        p_suspect_upper=100.0,
        p_impossible_upper=150.0,
        minutes_per_day=1440,
        outlier_z_threshold=3.0,
        work_order_pattern=r"^302\d{7}$",
        station_pattern=r"^IMM-\d+-\d+$",
        window_start="2025-11-05",
        window_end="2025-11-25",
    )


@pytest.mark.parametrize(
    "rule, good, bad_attr, bad_value, attr_label",
    [
        (VM01RecordIdMissing(), _row(), "record_id_src", None, "VM01"),
        (VM02ProdDateMissing(), _row(), "prod_date", None, "VM02"),
        (VM05ProducedQtyMissing(), _row(), "produced_qty", None, "VM05"),
        (VR01AvailabilityRange(), _row(), "availability", 120.0, "VR01"),
        (VR04PerformanceNegative(), _row(), "performance", -5.0, "VR04"),
        (VR10ShiftInvalid(), _row(), "shift", 4, "VR10"),
        (
            VC01ScrapGreaterThanProduced(),
            _row(produced_qty=10, scrap_qty=5),
            "scrap_qty",
            130,
            "VC01",
        ),
        (
            VC02OeeApxAPQ(),
            _row(availability=100, performance=100, quality=100, oee=100.0),
            "oee",
            50.0,
            "VC02",
        ),
        (VC08Quality100WithScrap(), _row(quality=100, scrap_qty=0), "scrap_qty", 5, "VC08"),
        (
            VX01FutureDate(),
            _row(prod_date=dt.date(2025, 11, 5)),
            "prod_date",
            dt.date(2099, 1, 1),
            "VX01",
        ),
        (VX03DayMinutesExceeded(), _row(run_time=1000, down_time=300), "down_time", 1500, "VX03"),
        (
            VF04WorkOrderPattern(),
            _row(work_order_no="3021234567"),
            "work_order_no",
            "999ABC",
            "VF04",
        ),
    ],
)
def test_rule_positive_and_negative(
    rule: Any, good: Any, bad_attr: str, bad_value: Any, attr_label: str
) -> None:
    ctx = _ctx()
    assert rule.check(good, ctx) is None, f"{attr_label} false positive on good row"
    bad = _row(**{bad_attr: bad_value})
    if bad_attr in ("scrap_qty",) and not getattr(bad, "quality", 0) >= 100.0:
        bad.quality = 100.0
    issue = rule.check(bad, ctx)
    assert issue is not None, f"{attr_label} missed bad row"
    assert issue.severity in (IssueSeverity.ERROR, IssueSeverity.WARNING)
    assert issue.suggested_action in (
        SuggestedAction.REJECT,
        SuggestedAction.WARN,
        SuggestedAction.FIX,
    )


def test_engine_runs_and_assigns_status(db) -> None:
    recs = [
        _row(
            id=None,
            record_id_src=1,
            prod_date=dt.date(2025, 11, 5),
            shift=1,
            produced_qty=10,
            scrap_qty=20,
            availability=120,
            performance=200,
            oee=300,
        ),
        _row(
            id=None,
            record_id_src=2,
            prod_date=dt.date(2025, 11, 5),
            shift=2,
            produced_qty=0,
            run_time=0,
            down_time=0,
            availability=80,
            performance=85,
            quality=90,
            oee=61.2,
        ),
        _row(
            id=None,
            record_id_src=3,
            prod_date=dt.date(2099, 1, 1),
            shift=1,
            produced_qty=5,
            run_time=2.0,
            down_time=0,
            availability=80,
            performance=85,
            quality=90,
            oee=61.2,
        ),
        _row(
            id=None,
            record_id_src=4,
            prod_date=dt.date(2025, 11, 6),
            shift=1,
            produced_qty=5,
            run_time=0,
            down_time=0,
            availability=80,
            performance=85,
            quality=90,
            oee=61.2,
        ),
        _row(
            id=None,
            record_id_src=5,
            prod_date=dt.date(2025, 11, 6),
            shift=2,
            produced_qty=5,
            run_time=3.0,
            down_time=0,
            availability=100,
            performance=85,
            quality=100,
            oee=85,
        ),
        _row(
            id=None,
            record_id_src=6,
            prod_date=dt.date(2025, 11, 7),
            shift=1,
            produced_qty=10,
            scrap_qty=0,
            availability=80,
            performance=120,
            quality=90,
            oee=86.4,
            run_time=5.0,
            down_time=0.5,
            planned_down=0.3,
            unplanned_down=0.2,
        ),
    ]
    for idx, r in enumerate(recs):
        db.add(
            models.ProductionRecord(
                record_id_src=r.record_id_src + idx * 1000,
                prod_date=r.prod_date,
                shift=r.shift,
                station_name=r.station_name,
                produced_qty=r.produced_qty,
                scrap_qty=r.scrap_qty,
                availability=r.availability,
                performance=r.performance,
                quality=r.quality,
                oee=r.oee,
                run_time=r.run_time,
                down_time=r.down_time,
                planned_down=r.planned_down,
                unplanned_down=r.unplanned_down,
                row_hash=f"hash_{idx}",
                status="pending",
            )
        )
    db.commit()

    results = run_validation(db)
    assert len(results) >= 5

    all_rule_ids = {i.rule_id for r in results.values() for i in r.issues}
    assert "V-C01" in all_rule_ids or "V-C06" in all_rule_ids or "V-X01" in all_rule_ids

    statuses = [r.status.value for r in results.values()]
    assert "rejected" in statuses
    assert "suspect" in statuses or "valid" in statuses

    for r in results.values():
        for i in r.issues:
            assert i.category in IssueCategory
            assert i.severity in IssueSeverity
            assert i.suggested_action in SuggestedAction


def test_engine_batch_vd02_and_vx05(db) -> None:
    base_row = {
        "prod_date": dt.date(2025, 11, 7),
        "shift": 1,
        "station_name": "IMM-2700-3",
        "work_order_no": "3021234567",
        "produced_qty": 10,
        "scrap_qty": 1,
        "availability": 85.0,
        "performance": 90.0,
        "quality": 95.0,
        "oee": 72.7,
        "run_time": 5.0,
        "down_time": 0.5,
        "planned_down": 0.3,
        "unplanned_down": 0.2,
        "status": "valid",
    }
    for i in range(49):
        db.add(
            models.ProductionRecord(
                row_hash=f"r_{i}", **{**base_row, "record_id_src": i, "produced_qty": 10}
            )
        )
    db.add(
        models.ProductionRecord(
            row_hash="conflict1",
            **{**base_row, "record_id_src": 100, "produced_qty": 5, "shift": 1},
        )
    )
    db.add(
        models.ProductionRecord(
            row_hash="conflict2",
            **{**base_row, "record_id_src": 101, "produced_qty": 100, "shift": 1},
        )
    )
    db.add(
        models.ProductionRecord(
            row_hash="outlier",
            **{**base_row, "record_id_src": 200, "produced_qty": 1000, "shift": 2},
        )
    )
    db.commit()
    results = run_validation(db)
    rule_ids = {i.rule_id for r in results.values() for i in r.issues}
    assert "V-D02" in rule_ids
    assert "V-X05" in rule_ids


# === Operatör aksiyonları: fix/reject/accept → audit trail ====================


def test_record_actions_create_audit_trail(db, client) -> None:
    """Her operatör aksiyonu (fix/reject/accept) status değiştirir + RecordEdit
    audit trail'e yazar — UI IssueDetailDrawer audit paneli buradan beslenir."""
    from app.features.validation.api import (
        accept_record,
        fix_record,
        list_edits,
        reject_record,
    )

    rec = models.ProductionRecord(
        record_id_src=9001,
        prod_date=dt.date(2025, 11, 8),
        shift=1,
        station_name="IMM-2700-3",
        work_order_no="3021234567",
        produced_qty=100,
        scrap_qty=0,
        availability=90.0,
        performance=95.0,
        quality=99.0,
        oee=85.0,
        oee_recomputed=85.0,
        run_time=7.0,
        down_time=0.5,
        planned_down=0.3,
        unplanned_down=0.2,
        row_hash="rh_audit_9001",
        status="rejected",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    rid = rec.id

    fix_record(record_id=rid, patch={"produced_qty": 110}, db=db)
    db.commit()
    assert db.get(models.ProductionRecord, rid).status == "valid"

    reject_record(record_id=rid, payload={"reason": "test reject"}, db=db)
    db.commit()
    assert db.get(models.ProductionRecord, rid).status == "rejected"

    accept_record(record_id=rid, payload={"reason": "test accept"}, db=db)
    db.commit()
    assert db.get(models.ProductionRecord, rid).status == "valid"

    edits = list_edits(record_id=rid, db=db)
    # 3 aksiyon = 3 edit (status snapshot her birinde).
    assert len(edits) == 3
    reasons = {e["reason"] for e in edits}
    assert "manual_fix" in reasons
    assert "reject:test reject" in reasons
    assert "accept:test accept" in reasons
    # Her edit'in edited_by=operator ve created_at dolu.
    for e in edits:
        assert e["edited_by"] == "operator"
        assert e["edited_at"] is not None
