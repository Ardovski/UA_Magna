"""Sync aggregator — yalnız status='valid' üretim kayıtlarını (date, shift) bazında
agrege eder ve hedef API'ye gidecek payload ile idempotency/hash alanlarını üretir.

Kritik kavramlar:
  - idempotency_key = '{YYYY-MM-DD}:{shift}' (DB'de unique) → aynı grubun
    mükerrer gönderimini engeller.
  - payload_hash    = canonical (sıralı anahtar, ayraçsız) JSON'un SHA-256'sı →
    içerik değişikliği tespiti.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.features.sync.target_constraints import check_target_constraints


def _canonical_json(payload: dict[str, Any]) -> str:
    # Canonical JSON: anahtarlar sıralı + boşluksuz ayraçlar → aynı içerik her zaman
    # aynı string'i (dolayısıyla aynı hash'i) üretir. Hash stabilitesi için şarttır.
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_hash(payload: dict[str, Any]) -> str:
    # payload_hash = canonical JSON'un SHA-256'sı. İçerik değişince hash değişir;
    # böylece zaten 'success' olmuş bir grubun payload'ı değiştiyse tespit edilebilir.
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _build_payload(
    production_date: dt.date,
    shift: int,
    machine_count: int,
    total_production_units: int,
    oe_value: float,
) -> dict[str, Any]:
    # Hedef API'ye gönderilecek payload'ın kanonik biçimi. Tipler kesin cast edilir
    # (int/float) ve oe_value 4 ondalığa yuvarlanır → hash'in deterministik olması için.
    return {
        "production_date": production_date.isoformat(),
        "shift": int(shift),
        "machine_count": int(machine_count),
        "total_production_units": int(total_production_units),
        "oe_value": float(round(oe_value, 4)),
    }


def _idempotency_key(production_date: dt.date, shift: int) -> str:
    # idempotency_key formatı: '{YYYY-MM-DD}:{shift}' — DB'de unique olduğu için
    # aynı (gün, vardiya) grubunun iki kez kayıt/gönderim oluşturması engellenir.
    return f"{production_date.isoformat()}:{int(shift)}"


def build_groups(db: Session) -> list[dict[str, Any]]:
    """Tüm valid kayıtları (date, shift) bazında agrege eden grup listesini üretir.

    Yalnız status='valid' ve prod_date/shift dolu kayıtlar dikkate alınır. Her grup için
    makine sayısı, toplam üretim, üretim-ağırlıklı OEE ve payload + idempotency_key + payload_hash
    hesaplanır. Üretimi olmayan (total_units <= 0) gruplar atlanır.

    Her grup dict'e `target_valid: bool` ve `target_issues: list[str]` eklenir — bunlar
    hedef API'nin kabul edeceği aralıklarda olup olmadığını gösterir (defense in depth;
    `submit()` bu alana göre gönderimi filtreler).
    """
    stmt = (
        select(
            models.ProductionRecord.prod_date.label("d"),
            models.ProductionRecord.shift.label("s"),
            func.count(func.distinct(models.ProductionRecord.station_name)).label("machine_count"),
            func.coalesce(func.sum(models.ProductionRecord.produced_qty), 0).label("total_units"),
            func.sum(
                models.ProductionRecord.oee_recomputed
                * func.coalesce(models.ProductionRecord.produced_qty, 0)
            ).label("oee_num"),
            func.sum(func.coalesce(models.ProductionRecord.produced_qty, 0)).label("oee_den"),
            func.count(models.ProductionRecord.id).label("record_count"),
        )
        .where(
            # Sadece 'valid' kayıtlar hedefe gider; hatalı/şüpheli veri asla agrege edilmez.
            models.ProductionRecord.status == "valid",
            models.ProductionRecord.prod_date.isnot(None),
            models.ProductionRecord.shift.isnot(None),
        )
        .group_by(models.ProductionRecord.prod_date, models.ProductionRecord.shift)
        .order_by(models.ProductionRecord.prod_date.asc(), models.ProductionRecord.shift.asc())
    )
    rows = db.execute(stmt).all()
    out: list[dict[str, Any]] = []
    for r in rows:
        production_date: dt.date = r.d
        shift: int = int(r.s)
        machine_count: int = int(r.machine_count or 0)
        total_units: int = int(r.total_units or 0)
        if total_units <= 0:
            continue  # Üretimi olmayan grup gönderilmez.
        # OEE, üretim adediyle ağırlıklandırılmış ortalama: Σ(oee*qty) / Σ(qty).
        oee_num = float(r.oee_num or 0.0)
        oee_den = float(r.oee_den or 0.0)
        oe_value: float = (oee_num / oee_den) if oee_den > 0 else 0.0
        payload = _build_payload(
            production_date=production_date,
            shift=shift,
            machine_count=machine_count,
            total_production_units=total_units,
            oe_value=oe_value,
        )
        ph = _payload_hash(payload)
        issues = check_target_constraints(
            {
                "production_date": production_date,
                "shift": shift,
                "machine_count": machine_count,
                "total_production_units": total_units,
                "oe_value": round(oe_value, 4),
            }
        )
        out.append(
            {
                "production_date": production_date,
                "shift": shift,
                "machine_count": machine_count,
                "total_production_units": total_units,
                "oe_value": round(oe_value, 4),
                "idempotency_key": _idempotency_key(production_date, shift),
                "payload_hash": ph,
                "payload": payload,
                "source_record_count": int(r.record_count or 0),
                "target_valid": not issues,
                "target_issues": issues,
            }
        )
    return out


def build_group(
    db: Session,
    production_date: dt.date,
    shift: int,
) -> dict[str, Any] | None:
    """Tek bir (production_date, shift) grubunu agrege eder; valid üretim yoksa None döner.

    build_groups ile aynı mantığı tek grup için uygular. Gönderim anında yeniden agregasyon
    için kullanılır — böylece payload her zaman güncel valid kayıtlardan türetilir.
    """
    stmt = select(
        func.count(func.distinct(models.ProductionRecord.station_name)).label("machine_count"),
        func.coalesce(func.sum(models.ProductionRecord.produced_qty), 0).label("total_units"),
        func.sum(
            models.ProductionRecord.oee_recomputed
            * func.coalesce(models.ProductionRecord.produced_qty, 0)
        ).label("oee_num"),
        func.sum(func.coalesce(models.ProductionRecord.produced_qty, 0)).label("oee_den"),
        func.count(models.ProductionRecord.id).label("record_count"),
    ).where(
        models.ProductionRecord.status == "valid",
        models.ProductionRecord.prod_date == production_date,
        models.ProductionRecord.shift == shift,
    )
    row = db.execute(stmt).one()
    total_units = int(row.total_units or 0)
    if total_units <= 0:
        return None
    machine_count = int(row.machine_count or 0)
    oee_num = float(row.oee_num or 0.0)
    oee_den = float(row.oee_den or 0.0)
    oe_value: float = (oee_num / oee_den) if oee_den > 0 else 0.0
    payload = _build_payload(production_date, shift, machine_count, total_units, oe_value)
    issues = check_target_constraints(
        {
            "production_date": production_date,
            "shift": int(shift),
            "machine_count": machine_count,
            "total_production_units": total_units,
            "oe_value": round(oe_value, 4),
        }
    )
    return {
        "production_date": production_date,
        "shift": int(shift),
        "machine_count": machine_count,
        "total_production_units": total_units,
        "oe_value": round(oe_value, 4),
        "idempotency_key": _idempotency_key(production_date, shift),
        "payload_hash": _payload_hash(payload),
        "payload": payload,
        "source_record_count": int(row.record_count or 0),
        "target_valid": not issues,
        "target_issues": issues,
    }
