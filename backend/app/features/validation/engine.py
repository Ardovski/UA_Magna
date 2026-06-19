"""Validation engine — iki geçişli (row + batch) değerlendirme.

Motor iki geçişte çalışır:
  PASS 1 (row-pass): Her kayıt tek başına ALL_RULES ile denetlenir. Bu kurallar
    saftır — yalnız o kaydın alanlarına ve bağlamdaki eşiklere bakar.
  PASS 2 (batch-pass): Tüm kayıt kümesi birlikte değerlendirilir. İki batch kuralı
    burada üretilir: V-D02 (iş anahtarı çakışması — aynı tarih/vardiya/istasyon/iş
    emri kovasında çelişen metrik) ve V-X05 (produced_qty z-score outlier'ı).

Her kaydın issue'larından statü türetilir (ERROR→rejected, WARNING→suspect, aksi
halde valid) ve ProductionRecord.status alanına yazılır. Issue'ların kendisi
`validation_issues` tablosuna YAZILMAZ; her çağrıda canlı yeniden üretilir.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.features.validation.models import (
    Issue,
    IssueCategory,
    IssueSeverity,
    RuleContext,
    SuggestedAction,
    ValidationResult,
)
from app.features.validation.rules.consistency import CONSISTENCY_RULES
from app.features.validation.rules.domain import DOMAIN_RULES
from app.features.validation.rules.duplicate import DUPLICATE_RULES
from app.features.validation.rules.format_ import FORMAT_RULES
from app.features.validation.rules.missing import MISSING_RULES
from app.features.validation.rules.range_ import RANGE_RULES

# PASS 1'de her kayda uygulanan saf kuralların düz listesi (6 kategori birleşik).
ALL_RULES: tuple[Any, ...] = (
    *MISSING_RULES,
    *RANGE_RULES,
    *CONSISTENCY_RULES,
    *DUPLICATE_RULES,
    *FORMAT_RULES,
    *DOMAIN_RULES,
)


def _build_context(current_file_hash: str | None = None) -> RuleContext:
    # Kurallara geçirilecek eşik/parametreleri uygulama ayarlarından (settings)
    # toplar — tolerans, performans şüphe/imkânsızlık üst sınırları, günlük dakika
    # bütçesi, outlier z-eşiği, regex desenleri ve rapor penceresi.
    return RuleContext(
        tolerance_pct=settings.validation_tolerance_pct,
        p_suspect_upper=settings.validation_p_suspect_upper,
        p_impossible_upper=settings.validation_p_impossible_upper,
        minutes_per_day=settings.validation_minutes_per_day,
        outlier_z_threshold=settings.validation_outlier_z_threshold,
        work_order_pattern=settings.validation_work_order_pattern,
        station_pattern=settings.validation_station_pattern,
        window_start=settings.validation_report_window_start,
        window_end=settings.validation_report_window_end,
    )


def _attach_ctx_dynamic(ctx: RuleContext, db: Session) -> RuleContext:
    # PASS 1 sırasında "görülenler" durumunu tutan dinamik alanları bağlar:
    # row_hash_seen / record_id_seen kayıt akışında duplicate (V-D01/V-D03) yakalar;
    # file_hash_seen daha önce import edilmiş CSV'leri (V-D04) tespit için DB'den gelir.
    ctx.row_hash_seen = set()
    ctx.record_id_seen = {}
    ctx.file_hash_seen = set(db.execute(select(models.ImportBatch.file_hash)).scalars().all())
    ctx.current_file_hash = None
    return ctx


def _check_row(record: Any, ctx: RuleContext) -> list[Issue]:
    # PASS 1: Tek kayda tüm saf kuralları uygular. Tek bir kuralın patlaması tüm
    # değerlendirmeyi düşürmesin diye her check() ayrı try ile izole edilir; hatalı
    # kural sessizce atlanır (kayıt yine de diğer kurallarca denetlenmeye devam eder).
    out: list[Issue] = []
    for rule in ALL_RULES:
        try:
            res = rule.check(record, ctx)
        except Exception:
            continue
        if res is None:
            continue
        if isinstance(res, list):
            out.extend(res)
        else:
            out.append(res)
    return out


def _zscore_outliers(values: list[int], threshold: float) -> set[int]:
    # V-X05'in çekirdeği: değerlerin z-skorunu hesaplar, |z| eşiği aşan değer
    # kümesini döner. İstatistik anlamlı olsun diye <5 örnekte veya std=0 ise
    # (tüm değerler aynı) hiç outlier işaretlenmez.
    if len(values) < 5:
        return set()
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(var) if var > 0 else 0.0
    if std == 0.0:
        return set()
    flagged: set[int] = set()
    for v in values:
        if abs((v - mean) / std) > threshold:
            flagged.add(int(v))
    return flagged


def _check_vd02_business_conflict(db: Session) -> dict[int, list[int]]:
    # PASS 2 — V-D02: Aynı iş anahtarı (tarih, vardiya, istasyon, iş emri) kovasında
    # birden çok kayıt varsa ve bunların metrikleri (produced/scrap/oee) birbirinden
    # FARKLI ise çelişki vardır; her çelişen kaydı diğer çakışan id'lerle eşler.
    # Not: Metrikler aynıysa bu salt tekrar olup V-D02 tetiklenmez.
    rows = db.execute(
        select(
            models.ProductionRecord.id,
            models.ProductionRecord.prod_date,
            models.ProductionRecord.shift,
            models.ProductionRecord.station_name,
            models.ProductionRecord.work_order_no,
            models.ProductionRecord.produced_qty,
            models.ProductionRecord.scrap_qty,
            models.ProductionRecord.oee,
        )
    ).all()
    # Kayıtları iş anahtarına göre kovala.
    bucket: dict[tuple[Any, Any, Any, Any], list[int]] = {}
    for r in rows:
        key = (r.prod_date, r.shift, r.station_name, r.work_order_no)
        bucket.setdefault(key, []).append(r[0])
    conflicts: dict[int, list[int]] = {}
    for _key, ids in bucket.items():
        if len(ids) < 2:
            continue  # Kovada tek kayıt varsa çakışma olamaz.
        rows_in_key = [next(rr for rr in rows if rr[0] == rid) for rid in ids]
        metrics: set[tuple[Any, ...]] = {
            (rr.produced_qty, rr.scrap_qty, rr.oee) for rr in rows_in_key
        }
        if len(metrics) > 1:  # Aynı anahtarda >1 farklı metrik seti → çelişki.
            for rid in ids:
                conflicts.setdefault(rid, []).extend([i for i in ids if i != rid])
    return conflicts


def _build_record_proxy(model: models.ProductionRecord) -> Any:
    # Kuralları ORM modeline doğrudan bağlamamak için kayıttan hafif bir okuma-amaçlı
    # proxy üretir; yalnız kuralların ihtiyaç duyduğu alanları kopyalar (gevşek bağ).
    proxy = type("R", (), {})()
    for col in (
        "id",
        "record_id_src",
        "prod_date",
        "work_order_no",
        "work_center_no",
        "work_center_name",
        "station_name",
        "stock_name",
        "shift",
        "availability",
        "performance",
        "quality",
        "oee",
        "run_time",
        "down_time",
        "planned_down",
        "unplanned_down",
        "produced_qty",
        "scrap_qty",
        "row_hash",
        "status",
    ):
        setattr(proxy, col, getattr(model, col))
    return proxy


def _vd05_outlier_flag(db: Session, ctx: RuleContext) -> dict[int, str]:
    # PASS 2 — V-X05: Tüm kayıtların produced_qty dağılımına bakar; z-score outlier
    # olan değerleri taşıyan kayıt id'lerini açıklayıcı mesajla işaretler. (Fonksiyon
    # adı vd05 tarihsel; ürettiği issue rule_id'si V-X05'tir.)
    rows = db.execute(
        select(
            models.ProductionRecord.id,
            models.ProductionRecord.produced_qty,
        )
    ).all()
    flagged: dict[int, str] = {}
    values = [int(r.produced_qty) for r in rows if r.produced_qty is not None]
    outliers = _zscore_outliers(values, ctx.outlier_z_threshold)
    for rid, pq in rows:
        if pq is not None and int(pq) in outliers:
            flagged[int(rid)] = (
                f"Üretim miktarı ({int(pq)}) istatistiksel outlier |z|>={ctx.outlier_z_threshold}."
            )
    return flagged


def _resolve_issues(
    results: dict[int, ValidationResult],
    conflict_map: dict[int, list[int]],
    outlier_map: dict[int, str],
) -> None:
    # PASS 2 sonuçlarını (outlier + iş anahtarı çakışması) ilgili kayıtların
    # ValidationResult'ına Issue olarak ekler. İkisi de WARNING/WARN olduğundan
    # bu kayıtları (başka ERROR yoksa) "suspect" statüsüne taşır.
    for rid, msg in outlier_map.items():
        results.setdefault(rid, ValidationResult(record_id=rid)).add(
            Issue(
                rule_id="V-X05",
                category=IssueCategory.DOMAIN,
                severity=IssueSeverity.WARNING,
                fields=("produced_qty",),
                message=msg,
                suggested_action=SuggestedAction.WARN,
            )
        )
    for rid, others in conflict_map.items():
        results.setdefault(rid, ValidationResult(record_id=rid)).add(
            Issue(
                rule_id="V-D02",
                category=IssueCategory.DUPLICATE,
                severity=IssueSeverity.WARNING,
                fields=("prod_date", "shift", "station_name", "work_order_no"),
                message=f"Çelişen kayıt(lar) var: ids={others}.",
                suggested_action=SuggestedAction.WARN,
            )
        )


def run_validation(
    db: Session,
    record_ids: Sequence[int] | None = None,
    current_file_hash: str | None = None,
) -> dict[int, ValidationResult]:
    # Bağlamı kur: statik eşikler + PASS 1 için dinamik "görülenler" durumu.
    ctx = _build_context(current_file_hash=current_file_hash)
    _attach_ctx_dynamic(ctx, db)

    # Hedef kayıtları yükle: record_ids verilmezse tüm kayıtlar, verilirse alt küme.
    if record_ids is None:
        models_iter = db.execute(select(models.ProductionRecord)).scalars().all()
    else:
        models_iter = (
            db.execute(
                select(models.ProductionRecord).where(models.ProductionRecord.id.in_(record_ids))
            )
            .scalars()
            .all()
        )

    # PASS 1 (row-pass): Her kaydı saf kurallarla denetle, sonucu biriktir.
    results: dict[int, ValidationResult] = {}
    for m in models_iter:
        proxy = _build_record_proxy(m)
        issues = _check_row(proxy, ctx)
        res = ValidationResult(record_id=m.id)
        res.extend(issues)
        results[m.id] = res

    # PASS 2 (batch-pass): Küme düzeyi V-D02 (iş anahtarı çakışması) ve V-X05
    # (outlier) bulgularını üret ve PASS 1 sonuçlarının üstüne ekle.
    conflict_map = _check_vd02_business_conflict(db)
    outlier_map = _vd05_outlier_flag(db, ctx)
    _resolve_issues(results, conflict_map, outlier_map)

    # Her kaydın nihai statüsünü issue'lardan türetip ProductionRecord'a yaz.
    # (Issue'ların kendisi DB'ye yazılmaz; yalnız türetilen status kalıcılaşır.)
    for m in models_iter:
        status = results[m.id].status
        m.status = status.value
    db.flush()
    return results


def summarize(results: dict[int, ValidationResult]) -> dict[str, Any]:
    # Sonuçları API/dashboard için toplulaştırır: statü/kategori/severity/kural
    # bazında sayımlar + toplam kayıt sayısı.
    by_category: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    by_rule: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    for r in results.values():
        by_status[r.status.value] += 1
        for i in r.issues:
            by_category[i.category.value] += 1
            by_severity[i.severity.value] += 1
            by_rule[i.rule_id] += 1
    return {
        "total_records": len(results),
        "by_status": dict(by_status),
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "by_rule": dict(by_rule),
    }
