"""Aralık dışı değer kuralları (V-R01..R10).

Sayısal alanların beklenen aralıkları dışına çıkmasını yakalar: A/P/Q/OEE yüzde
aralığı (0-100), negatif üretim/fire/süre, idealin üstünde performans (şüpheli
veya imkânsız), geçersiz vardiya (1/2/3 dışı). Performans üst sınırları ctx'ten
(p_suspect_upper / p_impossible_upper) okunur.
"""

from __future__ import annotations

from typing import Any

from app.features.validation.models import (
    Issue,
    IssueCategory,
    IssueSeverity,
    RuleContext,
    SuggestedAction,
)
from app.features.validation.rules.base import Rule


def _pct_ok(v: Any) -> bool:
    # Yüzde alanları 0..100 aralığında mı? (None dahil → henüz değerlendirme yapılamaz)
    return v is None or (isinstance(v, (int, float)) and 0.0 <= float(v) <= 100.0)


class VR01AvailabilityRange(Rule):
    id = "V-R01"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("availability",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.availability
        if v is None:
            return None
        if not (0.0 <= float(v) <= 100.0):
            return self.make_issue(f"availability={v} yüzde aralığı (0-100) dışında.")
        return None


class VR02QualityRange(Rule):
    id = "V-R02"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("quality",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.quality
        if v is None:
            return None
        if not (0.0 <= float(v) <= 100.0):
            return self.make_issue(f"quality={v} yüzde aralığı (0-100) dışında.")
        return None


class VR03OeeRange(Rule):
    id = "V-R03"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("oee",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.oee
        if v is None:
            return None
        if not (0.0 <= float(v) <= 100.0):
            return self.make_issue(f"oee={v} yüzde aralığı (0-100) dışında.")
        return None


class VR04PerformanceNegative(Rule):
    id = "V-R04"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("performance",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.performance
        if v is None:
            return None
        if float(v) < 0.0:
            return self.make_issue(f"performance={v} negatif olamaz.")
        return None


class VR05PerformanceSuspect(Rule):
    id = "V-R05"
    category = IssueCategory.RANGE
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("performance",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.performance
        if v is None:
            return None
        fv = float(v)
        if (
            ctx.p_suspect_upper < fv <= ctx.p_impossible_upper
        ):  # idealin üstü ama fiziksel olarak mümkün olabilir
            return self.make_issue(
                f"performance={fv} idealin üstünde; şüpheli (>{ctx.p_suspect_upper})."
            )
        return None


class VR06PerformanceImpossible(Rule):
    id = "V-R06"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("performance",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.performance
        if v is None:
            return None
        if float(v) > ctx.p_impossible_upper:
            return self.make_issue(
                f"performance={v} fiziksel olarak imkânsız (>{ctx.p_impossible_upper})."
            )
        return None


class VR07ProducedNegative(Rule):
    id = "V-R07"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("produced_qty",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.produced_qty
        if v is None:
            return None
        if int(v) < 0:
            return self.make_issue(f"produced_qty={v} negatif olamaz.")
        return None


class VR08ScrapNegative(Rule):
    id = "V-R08"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("scrap_qty",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.scrap_qty
        if v is None:
            return None
        if int(v) < 0:
            return self.make_issue(f"scrap_qty={v} negatif olamaz.")
        return None


class VR09DurationsNegative(Rule):
    id = "V-R09"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("run_time", "down_time", "planned_down", "unplanned_down")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        names = ("run_time", "down_time", "planned_down", "unplanned_down")
        bad: list[str] = []
        for n in names:
            v = getattr(record, n, None)
            if v is not None and float(v) < 0.0:
                bad.append(f"{n}={v}")
        if bad:
            return self.make_issue(f"Negatif süre: {', '.join(bad)}.")
        return None


class VR10ShiftInvalid(Rule):
    id = "V-R10"
    category = IssueCategory.RANGE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("shift",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.shift
        if v is None:
            return None
        if int(v) not in (1, 2, 3):  # 1=Sabah, 2=Öğle, 3=Gece — başka değer olamaz
            return self.make_issue(f"shift={v} geçerli vardiya dışı (1,2,3).")
        return None


RANGE_RULES: tuple[Rule, ...] = (
    VR01AvailabilityRange(),
    VR02QualityRange(),
    VR03OeeRange(),
    VR04PerformanceNegative(),
    VR05PerformanceSuspect(),
    VR06PerformanceImpossible(),
    VR07ProducedNegative(),
    VR08ScrapNegative(),
    VR09DurationsNegative(),
    VR10ShiftInvalid(),
)
