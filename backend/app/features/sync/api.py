"""Sync API router — preview / submit / history / retry uç noktaları.

Önemli: /submit ve /retry-all 202 (Accepted) döner; gönderim senkron yapılmaz, FastAPI
BackgroundTasks ile arka planda (`_run_in_background`) yürütülür. Böylece istek hızlıca yanıtlanır
ve retry/backoff gibi uzun süren işler HTTP isteğini bloklamaz.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.features.sync.schemas import SubmitRequest, SubmitResponse
from app.features.sync.service import (
    execute_pending,
    history,
    preview,
    retry_all,
    retry_submission,
    submit,
)

router = APIRouter()


@router.get("/preview")
def preview_endpoint(db: Session = Depends(get_db)) -> dict[str, object]:
    """Gönderilecek (gün, vardiya) gruplarını gönderim yapmadan önizler."""
    return preview(db).model_dump()


@router.post("/submit", status_code=202)
def submit_endpoint(
    payload: SubmitRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SubmitResponse:
    """Seçilen grup(lar) için pending submission oluşturur; 202 döner, gönderim arka planda yapılır.

    İstek: tek (production_date, shift), `targets` listesi ya da hiçbiri (tüm gruplar).
    Vardiya 1/2/3 dışındaysa 422 atılır. Yanıt accepted/skipped/rejected idempotency_key'lerini
    içerir.
    """
    if (
        payload.production_date is not None
        and payload.shift is not None
        and int(payload.shift) not in (1, 2, 3)
    ):
        raise HTTPException(status_code=422, detail="shift 1/2/3 olmalı")
    targets: list[tuple[dt.date, int]] | None = None
    if payload.targets:
        for t in payload.targets:
            if int(t.shift) not in (1, 2, 3):
                raise HTTPException(status_code=422, detail="shift 1/2/3 olmalı")
        targets = [(t.production_date, int(t.shift)) for t in payload.targets]
    response = submit(
        db,
        production_date=payload.production_date,
        shift=payload.shift,
        targets=targets,
        force=payload.force,
    )
    if response.submission_ids:
        # Gerçek HTTP gönderimi arka plana atılır → endpoint 202 ile hemen döner,
        # retry/backoff isteği bloklamaz.
        background.add_task(_run_in_background, response.submission_ids)
    return response


@router.get("/history")
def history_endpoint(
    status: Annotated[str | None, Query()] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Gönderim geçmişini (en yeni önce) döner; opsiyonel status filtresi ve limit."""
    items = history(db, limit=limit, status=status)
    return [i.model_dump() for i in items]


@router.post("/retry-all", status_code=202)
def retry_all_endpoint(
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """`failed`/`retrying` tüm gönderimleri arka planda yeniden dener → {queued}."""
    ids = retry_all(db)
    if ids:
        background.add_task(_run_in_background, ids)
    return {"queued": len(ids)}


@router.post("/{submission_id}/retry")
def retry_endpoint(
    submission_id: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Tek bir submission'ı senkron yeniden dener; bulunamazsa 404 verir."""
    out = retry_submission(db, submission_id)
    if out is None:
        raise NotFoundError(f"SyncSubmission {submission_id} bulunamadı.")
    return out.model_dump()


def _run_in_background(submission_ids: list[int]) -> None:
    # Arka plan görevi: request scope'undaki DB session'ı kullanılamaz (kapanmış olabilir),
    # bu yüzden yeni bir SessionLocal açılır ve finally'de mutlaka kapatılır.
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        execute_pending(db, submission_ids)
    finally:
        db.close()
