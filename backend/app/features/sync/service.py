"""Sync orchestrator — preview / submit / history / retry iş mantığı.

Akış: build_group/build_groups ile valid kayıtlar agrege edilir, idempotency_key (DB unique) ve
payload_hash kontrol edilerek pending SyncSubmission kayıtları oluşturulur. Gerçek gönderim
_attempt_send içinde retry matrisi + backoff uygulanarak yapılır. 'success' grup yeniden
gönderilmez (idempotency); payload değişmişse force ile yeniden gönderilebilir.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.features.sync.aggregator import build_group, build_groups
from app.features.sync.circuit import get_breaker
from app.features.sync.client import (
    PermanentSyncError,
    TransientSyncError,
    submit_payload,
)
from app.features.sync.retry import (
    compute_backoff,
    cooldown_after_rate_limit,
    is_retryable_status,
    should_retry,
)
from app.features.sync.schemas import (
    SubmissionOut,
    SubmitResponse,
    SyncGroupPreview,
    SyncPreview,
)

_logger = logging.getLogger("sync.service")


def _to_submission_out(row: models.SyncSubmission) -> SubmissionOut:
    return SubmissionOut(
        id=row.id,
        prod_date=row.prod_date,
        shift=row.shift,
        idempotency_key=row.idempotency_key,
        payload_hash=row.payload_hash,
        status=row.status,
        http_status=row.http_status,
        target_submission_id=row.target_submission_id,
        target_candidate_name=row.target_candidate_name,
        target_message=row.target_message,
        target_submitted_at=row.target_submitted_at,
        attempts=row.attempts,
        last_attempt_at=row.last_attempt_at,
        created_at=row.created_at,
        error_message=row.error_message,
        response_body=row.response_body,
    )


def preview(db: Session) -> SyncPreview:
    """Tüm valid grupları agrege edip gönderim yapmadan önizleme modeline çevirir.

    Hedef API constraint'lerine uymayan gruplar da listede gösterilir (target_valid=False
    + target_issues), ancak /submit'te gönderilmez. UI banner'da kaç grup uyumsuz
    sayıca gösterilir.
    """
    groups = build_groups(db)
    items = [
        SyncGroupPreview(
            production_date=g["production_date"],
            shift=g["shift"],
            machine_count=g["machine_count"],
            total_production_units=g["total_production_units"],
            oe_value=g["oe_value"],
            idempotency_key=g["idempotency_key"],
            payload_hash=g["payload_hash"],
            source_record_count=g["source_record_count"],
            target_valid=g.get("target_valid", True),
            target_issues=g.get("target_issues", []),
        )
        for g in groups
    ]
    not_compliant = sum(1 for it in items if not it.target_valid)
    return SyncPreview(
        groups=items,
        total_groups=len(items),
        not_target_compliant_count=not_compliant,
    )


def _existing(db: Session, idempotency_key: str) -> models.SyncSubmission | None:
    # idempotency_key DB'de unique olduğundan aynı (gün, vardiya) için en fazla bir kayıt olur.
    return (
        db.execute(
            select(models.SyncSubmission).where(
                models.SyncSubmission.idempotency_key == idempotency_key
            )
        )
        .scalars()
        .first()
    )


def _create_pending(
    db: Session,
    group: dict[str, Any],
) -> models.SyncSubmission:
    sub = models.SyncSubmission(
        prod_date=group["production_date"],
        shift=int(group["shift"]),
        idempotency_key=group["idempotency_key"],
        payload_hash=group["payload_hash"],
        status="pending",
        http_status=None,
        target_submission_id=None,
        attempts=0,
        last_attempt_at=None,
        error_message=None,
        response_body=None,
    )
    db.add(sub)
    db.flush()
    return sub


def _attempt_send(
    db: Session,
    sub: models.SyncSubmission,
    payload: dict[str, Any],
) -> bool:
    """Payload'ı retry matrisi + backoff ile gönderir; başarılıysa True döner.

    Döngü mantığı:
      - TransientSyncError (ağ/timeout): should_retry True ise backoff'tan sonra yeniden dener,
        değilse 'failed'.
      - PermanentSyncError (401/422/413): asla yeniden denenmez, doğrudan 'failed'.
      - 2xx: 'success' (varsa target_submission_id yakalanır).
      - 429/5xx: retry edilebilir → should_retry'a göre yeniden dener (429'da cooldown).
      - Diğer 4xx: kalıcı → 'failed'.
    """
    for attempt in range(1, settings.target_api_max_retries + 1):
        sub.attempts = int(attempt)
        sub.last_attempt_at = dt.datetime.now(dt.UTC)
        try:
            status, body = submit_payload(
                payload=payload,
                idempotency_key=sub.idempotency_key,
            )
        except TransientSyncError as exc:
            # Geçici hata (ağ/timeout) → retry edilebilir. Önce 'retrying' işaretlenir.
            sub.status = "retrying"
            sub.error_message = exc.message
            sub.response_body = None
            db.flush()
            if not should_retry(attempt=attempt, exc=exc):
                sub.status = "failed"
                db.flush()
                _logger.warning(
                    "sync.exhausted idem=%s attempts=%d",
                    sub.idempotency_key,
                    sub.attempts,
                )
                return False
            _sleep_cooldown_if_429(None, attempt=attempt)
            continue
        except PermanentSyncError as exc:
            # Kalıcı hata (örn. 401/422/413) → retry YOK, doğrudan 'failed'.
            sub.status = "failed"
            sub.http_status = exc.status_code
            sub.error_message = exc.message
            sub.response_body = json.dumps({"detail": exc.message}, ensure_ascii=False)[:2000]
            db.flush()
            return False

        sub.http_status = status
        sub.response_body = json.dumps(body, ensure_ascii=False, default=str)[:2000]

        if 200 <= status < 300:
            sub.status = "success"
            # Hedef API'nin beklenen başarılı yanıtı (case §5.5):
            # {success, submission_id, candidate_name, message, submitted_at}.
            # Hataları sessize almadan mümkün olduğunca çok alanı yakalayıp operatöre gösteririz.
            if isinstance(body, dict):
                sid = body.get("submission_id")
                if isinstance(sid, int):
                    sub.target_submission_id = sid
                cname = body.get("candidate_name")
                if isinstance(cname, str) and cname.strip():
                    sub.target_candidate_name = cname.strip()[:120]
                msg = body.get("message")
                if isinstance(msg, str) and msg.strip():
                    sub.target_message = msg.strip()
                sub_at_raw = body.get("submitted_at")
                if isinstance(sub_at_raw, str) and sub_at_raw.strip():
                    try:
                        sub.target_submitted_at = dt.datetime.fromisoformat(sub_at_raw.strip())
                    except ValueError:
                        # Format tanınmadı → ham metni message'a ekle (kaybolmasın).
                        sub.target_message = (
                            f"{sub.target_message or ''} [submitted_at: {sub_at_raw.strip()}]"
                        ).strip()
            sub.error_message = None
            db.flush()
            return True

        if is_retryable_status(status):
            sub.status = "retrying"
            sub.error_message = f"http {status} retrying"
            db.flush()
            if not should_retry(attempt=attempt, status_code=status):
                sub.status = "failed"
                db.flush()
                return False
            _sleep_cooldown_if_429(status, attempt=attempt)
            continue

        sub.status = "failed"
        sub.error_message = f"http {status} permanent"
        db.flush()
        return False

    sub.status = "failed"
    sub.error_message = "max attempts reached"
    db.flush()
    return False


def _sleep_cooldown_if_429(status: int | None, attempt: int) -> None:
    import time

    if status == 429:
        time.sleep(cooldown_after_rate_limit())
        return
    time.sleep(compute_backoff(attempt))


def submit(
    db: Session,
    production_date: dt.date | None = None,
    shift: int | None = None,
    targets: list[tuple[dt.date, int]] | None = None,
    force: bool = False,
) -> SubmitResponse:
    response = SubmitResponse()
    if targets:
        # Kullanıcının seçtiği belirli (gün, vardiya) grupları — sadece bunlar gider.
        groups = [g for (d, s) in targets if (g := build_group(db, d, s)) is not None]
    elif production_date is not None and shift is not None:
        group = build_group(db, production_date, shift)
        if group is None:
            return response
        groups = [group]
    else:
        groups = build_groups(db)

    for group in groups:
        # Hedef API constraint ihlali (oe_value aralık dışı, gelecek tarih, vb.) →
        # gönderim hiç denemez; idempotency_key rejected_target_constraints'a düşer.
        # Operatör UI'da sebebi görüp veriyi düzeltebilir.
        if not group.get("target_valid", True):
            response.rejected_target_constraints.append(group["idempotency_key"])
            _logger.info(
                "sync.skip.target_constraints idem=%s issues=%s",
                group["idempotency_key"],
                group.get("target_issues"),
            )
            continue
        existing = _existing(db, group["idempotency_key"])
        if existing is not None and existing.status == "success":
            if existing.payload_hash == group["payload_hash"]:
                response.skipped_already_success.append(group["idempotency_key"])
                continue
            if not force:
                response.rejected_due_to_hash_conflict.append(group["idempotency_key"])
                continue
        if existing is None or force:
            sub = _create_pending(db, group)
            response.accepted.append(group["idempotency_key"])
            response.submission_ids.append(sub.id)
        else:
            sub = existing
            sub.status = "pending"
            db.flush()
            response.accepted.append(group["idempotency_key"])
            response.submission_ids.append(sub.id)
    db.commit()
    return response


def execute_pending(
    db: Session,
    submission_ids: list[int],
) -> list[int]:
    success_ids: list[int] = []
    if not submission_ids:
        return success_ids
    rows = (
        db.execute(
            select(models.SyncSubmission).where(models.SyncSubmission.id.in_(submission_ids))
        )
        .scalars()
        .all()
    )
    breaker = get_breaker()
    for sub in rows:
        # Circuit breaker OPEN ise hedefe hiç gitme — submission'ı failed işaretle.
        if not breaker.allow():
            sub.status = "failed"
            sub.error_message = "circuit_open: hedef API geçici olarak duraklatıldı"
            db.flush()
            continue
        group = build_group(db, sub.prod_date, sub.shift)
        if group is None:
            sub.status = "failed"
            sub.error_message = "no valid records to aggregate"
            db.flush()
            continue
        # Arka planda çalışırken aradaki zamanda constraint ihlali oluşmuş olabilir
        # (ör. manuel onayla sınırları aşan bir kayıt eklendiyse) — savunma amaçlı kontrol.
        if not group.get("target_valid", True):
            sub.status = "failed"
            sub.error_message = f"target_constraints_violated: {group.get('target_issues')}"
            db.flush()
            _logger.warning(
                "sync.skip.target_constraints idem=%s issues=%s",
                sub.idempotency_key,
                group.get("target_issues"),
            )
            continue
        if group["payload_hash"] != sub.payload_hash:
            sub.payload_hash = group["payload_hash"]
            sub.status = "pending"
            db.flush()
        ok = _attempt_send(db, sub, group["payload"])
        if ok:
            breaker.record_success()
            success_ids.append(sub.id)
        else:
            breaker.record_failure()
    db.commit()
    return success_ids


def history(
    db: Session,
    limit: int = 100,
    status: str | None = None,
) -> list[SubmissionOut]:
    stmt = select(models.SyncSubmission).order_by(models.SyncSubmission.id.desc()).limit(limit)
    if status is not None:
        stmt = stmt.where(models.SyncSubmission.status == status)
    rows = db.execute(stmt).scalars().all()
    return [_to_submission_out(r) for r in rows]


def retry_all(db: Session) -> list[int]:
    """`failed`/`retrying` tüm submission'ları yeniden kuyruğa al (`pending`) → id listesi.

    Gerçek gönderim çağırana (endpoint) bırakılır: id'ler `execute_pending`'e arka planda
    verilir (her grup göndermeden önce yeniden agrege edilir).
    """
    rows = (
        db.execute(
            select(models.SyncSubmission).where(
                models.SyncSubmission.status.in_(["failed", "retrying"])
            )
        )
        .scalars()
        .all()
    )
    ids: list[int] = []
    for sub in rows:
        sub.status = "pending"
        sub.error_message = None
        ids.append(sub.id)
    db.commit()
    return ids


def retry_submission(
    db: Session,
    submission_id: int,
) -> SubmissionOut | None:
    sub = db.get(models.SyncSubmission, submission_id)
    if sub is None:
        return None
    if sub.status == "success":
        return _to_submission_out(sub)
    group = build_group(db, sub.prod_date, sub.shift)
    if group is None:
        sub.status = "failed"
        sub.error_message = "no valid records to aggregate"
        db.commit()
        return _to_submission_out(sub)
    sub.payload_hash = group["payload_hash"]
    sub.status = "pending"
    sub.error_message = None
    db.flush()
    _attempt_send(db, sub, group["payload"])
    db.commit()
    return _to_submission_out(sub)
