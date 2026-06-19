"""Ingestion API router — preview + import + batch management endpoint'leri."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.ingestion.schemas import BatchOut, ImportPreview, ImportSummary
from app.features.ingestion.service import (
    delete_batch,
    get_active_batch_id,
    import_csv,
    list_batches,
    preview_csv,
    set_active_batch,
)

router = APIRouter()


@router.post("/preview", response_model=ImportPreview)
def preview(file: UploadFile = File(...)) -> ImportPreview:
    """CSV'yi DB'ye yazmadan önizler: kolon tespiti, encoding ve örnek satırlar."""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="filename gerekli")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="dosya boş")
    return preview_csv(data, file.filename)


@router.post("/import", response_model=ImportSummary)
def import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportSummary:
    """CSV'yi normalize edip DB'ye import eder; ardından otomatik validasyon çalışır."""
    if file.filename is None:
        raise HTTPException(status_code=400, detail="filename gerekli")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="dosya boş")
    return import_csv(db, data, file.filename)


@router.get("/batches", response_model=list[BatchOut])
def list_batches_endpoint(db: Session = Depends(get_db)) -> list[BatchOut]:
    """Tüm import batch'lerini (en yeni önce) listeler."""
    return list_batches(db)


@router.get("/batches/active", response_model=BatchOut | None)
def get_active_batch_endpoint(db: Session = Depends(get_db)) -> BatchOut | None:
    """Aktif batch'i döner; yoksa veya geçersizse None."""
    active_id: int | None = get_active_batch_id(db)
    if active_id is None:
        return None
    try:
        return set_active_batch(db, active_id)
    except ValueError:
        return None


@router.post("/batches/{batch_id}/activate", response_model=BatchOut)
def activate_batch_endpoint(
    batch_id: int,
    db: Session = Depends(get_db),
) -> BatchOut:
    """Verilen batch'i aktif batch olarak işaretler (dashboard bunu baz alır)."""
    try:
        result: BatchOut = set_active_batch(db, batch_id)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/batches/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_endpoint(
    batch_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Batch'i ve ona bağlı tüm üretim kayıtlarını siler."""
    try:
        delete_batch(db, batch_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return None
