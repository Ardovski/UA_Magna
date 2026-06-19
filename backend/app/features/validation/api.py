"""Validation API router — motoru çağırıp sonuçları HTTP uçlarına bağlar.

Uçlar: /run (seçili veya tüm kayıtları doğrula), /summary, /issues (canlı düzleştirilmiş
+ filtreli liste), /report ve /report.xlsx (indirilebilir rapor). Ayrıca operatör
aksiyonları: kaydı düzelt/reddet/onayla ve düzenleme (RecordEdit) geçmişi. Router
incedir; gerçek değerlendirme engine'de yapılır.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db import models
from app.db.session import get_db
from app.features.validation.engine import run_validation, summarize
from app.features.validation.models import (
    IssueCategory,
    IssueSeverity,
)
from app.features.validation.report import full_report, report_xlsx

router = APIRouter()


# Validasyonu tetikler; record_ids verilirse alt küme, yoksa tüm kayıtlar denetlenir.
# Türetilen statüler kayıtlara yazıldığı için sonucu commit ederiz.
@router.post("/run")
def run(
    record_ids: list[int] | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    results = run_validation(db, record_ids=record_ids)
    db.commit()
    return {"summary": summarize(results), "record_count": len(results)}


# Tüm kayıtlar için özet sayımları döner (statü/kategori/severity/kural dağılımı).
@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict[str, object]:
    results = run_validation(db)
    db.commit()
    return summarize(results)


# Issue listesini canlı üretip kategori/severity/rule_id/record_status'a göre filtreler.
@router.get("/issues")
def issues(
    category: IssueCategory | None = None,
    severity: IssueSeverity | None = None,
    rule_id: str | None = None,
    record_status: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    # Issue'lar `validation_issues` tablosunda kalıcı tutulmuyor; tek doğruluk
    # kaynağı motorun anlık çıktısıdır (summary/report ile aynı yol). Bu yüzden
    # tabloyu okumak yerine `run_validation` sonucunu düzleştirip döneriz —
    # aksi halde liste her zaman boş gelir.
    results = run_validation(db)
    db.commit()
    # Issue'lar kalıcı olmadığından gerçek bir PK yok; UI listesi için sıralı yapay
    # bir `id` üretiriz (detected_at/fixed_at de bu yüzden None döner).
    out: list[dict[str, object]] = []
    next_id = 1
    for record_id, result in results.items():
        rec_status = result.status.value
        if record_status is not None and rec_status != record_status:
            continue
        for issue in result.issues:
            if category is not None and issue.category != category:
                continue
            if severity is not None and issue.severity != severity:
                continue
            if rule_id is not None and issue.rule_id != rule_id:
                continue
            out.append(
                {
                    "id": next_id,
                    "record_id": record_id,
                    "rule_id": issue.rule_id,
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "fields": ", ".join(issue.fields) if issue.fields else None,
                    "message": issue.message,
                    "suggested_action": issue.suggested_action.value,
                    "detected_at": None,
                    "fixed_at": None,
                    "status": rec_status,
                }
            )
            next_id += 1
    return out


# Tam JSON rapor: özet + sistemik/tekil kural ayrımı + kayıt başına issue detayı.
@router.get("/report")
def report(db: Session = Depends(get_db)) -> dict[str, object]:
    results = run_validation(db)
    db.commit()
    return full_report(results)


_XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/report.xlsx")
def report_xlsx_endpoint(db: Session = Depends(get_db)) -> Response:
    """İndirilebilir validation raporu (.xlsx) — Özet + Issues + Sistemik/Tekil sayfaları."""
    results = run_validation(db)
    db.commit()
    return Response(
        content=report_xlsx(results),
        media_type=_XLSX_MEDIA,
        headers={
            "Content-Disposition": 'attachment; filename="validation_report.xlsx"',
            "Cache-Control": "no-store",
        },
    )


# Kaydı id ile getirir; yoksa 404 fırlatır (operatör aksiyonlarında ortak yardımcı).
def _record_or_404(db: Session, record_id: int) -> models.ProductionRecord:
    rec = db.get(models.ProductionRecord, record_id)
    if rec is None:
        raise NotFoundError(f"Record {record_id} bulunamadı.")
    return rec


def _to_dict(rec: models.ProductionRecord) -> dict[str, object]:
    return {c.name: getattr(rec, c.name) for c in rec.__table__.columns}


# Operatör düzeltmesi: verilen patch'i kayda uygula, statüyü "valid"e çek ve
# eski→yeni snapshot'ı RecordEdit denetim kaydı olarak sakla.
@router.post("/records/{record_id}/fix")
def fix_record(
    record_id: int,
    patch: dict[str, object],
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rec = _record_or_404(db, record_id)
    before = _to_dict(rec)
    for k, v in patch.items():
        if hasattr(rec, k):
            setattr(rec, k, v)
    rec.status = "valid"
    db.add(
        models.RecordEdit(
            record_id=rec.id,
            field="status",
            old_value=json.dumps(before, default=str, ensure_ascii=False),
            new_value=json.dumps(_to_dict(rec), default=str, ensure_ascii=False),
            reason="manual_fix",
            edited_by="operator",
        )
    )
    db.flush()
    return {"record_id": rec.id, "status": rec.status}


# Operatör reddi: kaydı "rejected" yapar (hedef API'ye gitmez) + denetim kaydı tutar.
@router.post("/records/{record_id}/reject")
def reject_record(
    record_id: int,
    payload: dict[str, object] | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rec = _record_or_404(db, record_id)
    reason_in = (payload or {}).get("reason")
    before = _to_dict(rec)
    rec.status = "rejected"
    db.add(
        models.RecordEdit(
            record_id=rec.id,
            field="status",
            old_value=json.dumps(before, default=str, ensure_ascii=False),
            new_value=json.dumps(_to_dict(rec), default=str, ensure_ascii=False),
            reason=f"reject:{reason_in}" if reason_in else "reject",
            edited_by="operator",
        )
    )
    db.flush()
    return {"record_id": rec.id, "status": rec.status}


# Operatör onayı: şüpheli (suspect) bir kaydı manuel olarak "valid" kabul eder +
# denetim kaydı tutar (yanlış pozitifleri geçirme yolu).
@router.post("/records/{record_id}/accept")
def accept_record(
    record_id: int,
    payload: dict[str, object] | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rec = _record_or_404(db, record_id)
    reason_in = (payload or {}).get("reason")
    before = _to_dict(rec)
    rec.status = "valid"
    db.add(
        models.RecordEdit(
            record_id=rec.id,
            field="status",
            old_value=json.dumps(before, default=str, ensure_ascii=False),
            new_value=json.dumps(_to_dict(rec), default=str, ensure_ascii=False),
            reason=f"accept:{reason_in}" if reason_in else "accept",
            edited_by="operator",
        )
    )
    db.flush()
    return {"record_id": rec.id, "status": rec.status}


# Bir kaydın düzenleme/aksiyon geçmişini (RecordEdit) en yeniden eskiye döner.
@router.get("/records/{record_id}/edits")
def list_edits(
    record_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    rec = _record_or_404(db, record_id)
    rows = (
        db.execute(
            select(models.RecordEdit)
            .where(models.RecordEdit.record_id == rec.id)
            .order_by(models.RecordEdit.edited_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "field": r.field,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "reason": r.reason,
            "edited_by": r.edited_by,
            "edited_at": r.edited_at.isoformat() if r.edited_at else None,
        }
        for r in rows
    ]
