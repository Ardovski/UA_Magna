"""Domain / fiziksel imkânsız kurallar (V-X01..X06).

İş alanının izin vermediği değerleri yakalar: gelecek tarih, rapor penceresi dışı
tarih, 1 günü aşan süre, plansız duruşun toplamdan büyük olması, üretim outlier'ı
(batch-pass'te hesaplanır) ve OEE=0 + tam üretim çelişkisi. V-X01/03/04 ERROR
(reddedilir); geri kalanı WARNING (şüpheli).
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from app.features.validation.models import (
    Issue,
    IssueCategory,
    IssueSeverity,
    RuleContext,
    SuggestedAction,
)
from app.features.validation.rules.base import Rule


class VX01FutureDate(Rule):
    id = "V-X01"
    category = IssueCategory.DOMAIN
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("prod_date",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        d = record.prod_date
        if d is None:
            return None
        today = dt.date.today()
        if d > today:
            return self.make_issue(
                f"prod_date={d} gelecek tarih; imkânsız."
            )  # ileri tarihli kayıt olamaz
        return None


class VX02OutsideReportWindow(Rule):
    id = "V-X02"
    category = IssueCategory.DOMAIN
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("prod_date",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        d = record.prod_date
        if d is None:
            return None
        try:
            start = dt.date.fromisoformat(ctx.window_start)
            end = dt.date.fromisoformat(ctx.window_end)
        except ValueError:
            return None
        if d < start or d > end:
            return self.make_issue(
                f"prod_date={d} rapor penceresi dışında ({ctx.window_start}..{ctx.window_end})."
            )
        return None


class VX03DayMinutesExceeded(Rule):
    id = "V-X03"
    category = IssueCategory.DOMAIN
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("run_time", "down_time")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        rt = record.run_time or 0.0
        d = record.down_time or 0.0
        total = float(rt) + float(d)  # Çalışma + duruş toplamı 1 vardiya/gün dakikasını aşamaz
        if total > float(ctx.minutes_per_day):
            return self.make_issue(
                f"Çalışma+Duruş={total} > {ctx.minutes_per_day} dk (1 gün sınırı)."
            )
        return None


class VX04UnplannedDownExceedsTotal(Rule):
    id = "V-X04"
    category = IssueCategory.DOMAIN
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("unplanned_down", "run_time", "planned_down")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        ud = record.unplanned_down
        rt = record.run_time or 0.0
        pd_v = record.planned_down or 0.0
        if ud is None:
            return None
        if float(ud) > (float(rt) + float(ud) + float(pd_v)):
            return self.make_issue("Plansız duruş, mevcut toplam süreden büyük olamaz.")
        return None


class VX05ProducedOutlier(Rule):
    id = "V-X05"
    category = IssueCategory.DOMAIN
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("produced_qty",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        p = record.produced_qty
        if p is None:
            return None
        return None


class VX06ZeroOeeWithFullRun(Rule):
    id = "V-X06"
    category = IssueCategory.DOMAIN
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("oee", "produced_qty", "run_time")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        oee = record.oee
        p = record.produced_qty
        rt = record.run_time
        if None in (oee, p, rt):
            return None
        if float(oee) == 0.0 and int(p) > 0 and float(rt) > 0.0:
            return self.make_issue(
                "OEE=0 ama tam üretim+çalışma var → ölçüm hatası olabilir."
            )  # ölçüm kopması
        return None


DOMAIN_RULES: tuple[Rule, ...] = (
    VX01FutureDate(),
    VX02OutsideReportWindow(),
    VX03DayMinutesExceeded(),
    VX04UnplannedDownExceedsTotal(),
    VX05ProducedOutlier(),
    VX06ZeroOeeWithFullRun(),
)
