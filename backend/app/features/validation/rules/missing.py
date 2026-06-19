"""Eksik/boş veri kuralları (V-M01..M07).

Zorunlu alanların (record_id, prod_date, shift, station, produced_qty) ve/veya
OEE bileşenlerinin bir kısmının boş olmasını yakalar. İlk 5'i ERROR (kayıt
reddedilir); M06/M07 WARNING (şüpheli — operatöre bildirilir).
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


def _is_blank(value: Any) -> bool:
    # None ya da yalnız boşluk içeren string → boş sayılır.
    return value is None or (isinstance(value, str) and value.strip() == "")


class VM01RecordIdMissing(Rule):
    id = "V-M01"
    category = IssueCategory.MISSING
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("record_id",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        if _is_blank(record.record_id_src):
            return self.make_issue("record_id boş; PK yok → kayıt izlenemez.")
        return None


class VM02ProdDateMissing(Rule):
    id = "V-M02"
    category = IssueCategory.MISSING
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("prod_date",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        if _is_blank(record.prod_date):
            return self.make_issue("prod_date boş; gün/vardiya kovasına atanamaz.")
        return None


class VM03ShiftMissing(Rule):
    id = "V-M03"
    category = IssueCategory.MISSING
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("shift",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        if _is_blank(record.shift):
            return self.make_issue("shift boş; vardiya bazlı gruplama yapılamaz.")
        return None


class VM04StationMissing(Rule):
    id = "V-M04"
    category = IssueCategory.MISSING
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("station_name",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        if _is_blank(record.station_name):
            return self.make_issue("station_name boş; temel boyut eksik.")
        return None


class VM05ProducedQtyMissing(Rule):
    id = "V-M05"
    category = IssueCategory.MISSING
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("produced_qty",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        if _is_blank(record.produced_qty):
            return self.make_issue("produced_qty boş; çekirdek metrik eksik.")
        return None


class VM06OeeComponentsMissing(Rule):
    id = "V-M06"
    category = IssueCategory.MISSING
    severity = IssueSeverity.WARNING
    action = SuggestedAction.FIX
    fields = ("oee", "availability", "performance", "quality")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        oee = record.oee
        a = record.availability
        p = record.performance
        q = record.quality
        comps = [a, p, q]
        non_null = sum(1 for v in comps if v is not None) + (1 if oee is not None else 0)
        # 4'ünden bir kısmı (ama hepsi değil) boşsa ve yeniden hesaplanabiliyorsa uyar.
        if 0 < non_null < 4 and (oee is None or any(c is None for c in comps)):
            return self.make_issue(
                "OEE bileşenlerinden biri eksik; formülden yeniden hesaplanabilir."
            )
        return None


class VM07OptionalDimsMissing(Rule):
    id = "V-M07"
    category = IssueCategory.MISSING
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("stock_name", "work_center_no", "work_center_name")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        blanks = []
        if _is_blank(record.stock_name):
            blanks.append("stock_name")
        if _is_blank(record.work_center_no):
            blanks.append("work_center_no")
        if _is_blank(record.work_center_name):
            blanks.append("work_center_name")
        if not blanks:
            return None
        return self.make_issue(f"Opsiyonel boyut(lar) boş: {', '.join(blanks)}.")  # bilgi amaçlı


MISSING_RULES: tuple[Rule, ...] = (
    VM01RecordIdMissing(),
    VM02ProdDateMissing(),
    VM03ShiftMissing(),
    VM04StationMissing(),
    VM05ProducedQtyMissing(),
    VM06OeeComponentsMissing(),
    VM07OptionalDimsMissing(),
)
