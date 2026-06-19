"""Tutarsız ilişki kuralları (V-C01..C10).

Birden fazla alan arasındaki matematiksel/işsel çelişkileri yakalar: fire>üretim,
OEE≠A·P·Q, Q≠(Üretim-Fire)/Üretim, duruş toplamları vb. Ağırlıklı olarak WARNING
(şüpheli), ancak bariz fiziksel imkânsızlıklar (V-C01, V-C06, V-C08) ERROR →
kayıt reddedilir.
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


def _diff(a: float, b: float) -> float:
    return abs(float(a) - float(b))


class VC01ScrapGreaterThanProduced(Rule):
    id = "V-C01"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("scrap_qty", "produced_qty")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        s = record.scrap_qty
        p = record.produced_qty
        if s is None or p is None:
            return None
        if int(s) > int(p):
            return self.make_issue(
                f"Fire ({s}) üretimden ({p}) fazla."
            )  # fiziksel imkânsız → reject
        return None


class VC02OeeApxAPQ(Rule):
    id = "V-C02"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("oee", "availability", "performance", "quality")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        oee = record.oee
        a = record.availability
        p = record.performance
        q = record.quality
        if None in (oee, a, p, q):
            return None
        # OEE = A·P·Q/10000 (yüzde). tolerance_pct kadar sapma tolere edilir; üstü çelişki.
        expected = (float(a) * float(p) * float(q)) / 10000.0
        if _diff(float(oee), expected) > ctx.tolerance_pct:
            return self.make_issue(
                f"OEE={oee} ≠ A·P·Q/10000={expected:.2f} (tol={ctx.tolerance_pct})."
            )
        return None


class VC03QualityVsScrap(Rule):
    id = "V-C03"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("quality", "produced_qty", "scrap_qty")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        q = record.quality
        p = record.produced_qty
        s = record.scrap_qty
        if None in (q, p, s) or int(p) == 0:
            return None
        expected = (float(p) - float(s)) / float(p) * 100.0  # Q tanımı: iyi/(iyi+hatalı)·100
        if _diff(float(q), expected) > ctx.tolerance_pct:
            return self.make_issue(
                f"Q={q} ≠ (Üretim-Fire)/Üretim·100={expected:.2f} (tol={ctx.tolerance_pct})."
            )
        return None


class VC04AvailabilityVsRunTime(Rule):
    id = "V-C04"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("availability", "run_time", "unplanned_down")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        a = record.availability
        rt = record.run_time
        ud = record.unplanned_down
        if None in (a, rt, ud):
            return None
        denom = float(rt) + float(ud)
        if denom <= 0.0:
            return None  # 0/0 → bölünemez; kural burada sessiz kalır (V-M* eksik alanla uğraşır).
        # A = Çalışma / (Çalışma + Plansız Duruş) · 100
        expected = float(rt) / denom * 100.0
        if _diff(float(a), expected) > ctx.tolerance_pct:
            return self.make_issue(f"A={a} ≠ Çalışma/(Çalışma+Plansız)·100={expected:.2f}.")
        return None


class VC05DownTimeBreakdown(Rule):
    id = "V-C05"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("down_time", "planned_down", "unplanned_down")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        d = record.down_time
        pd_v = record.planned_down
        ud = record.unplanned_down
        if None in (d, pd_v, ud):
            return None
        expected = float(pd_v) + float(ud)  # Toplam duruş, planlı+plansız toplamına eşit olmalı.
        if _diff(float(d), expected) > ctx.tolerance_pct:
            return self.make_issue(
                f"Duruş={d} ≠ Planlı+Plansız={expected:.2f} (tol={ctx.tolerance_pct})."
            )
        return None


class VC06ProducedWithoutRunTime(Rule):
    id = "V-C06"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("produced_qty", "run_time")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        p = record.produced_qty
        rt = record.run_time
        if p is None:
            return None
        if int(p) > 0 and (rt is None or float(rt) == 0.0):
            return self.make_issue(
                "Üretim>0 ama Çalışma Süresi=0 → imkânsız."
            )  # çalışmadan üretim yok
        return None


class VC07RunWithoutProductionNoDown(Rule):
    id = "V-C07"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("run_time", "produced_qty", "down_time")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        rt = record.run_time
        p = record.produced_qty
        d = record.down_time
        if None in (rt, p, d):
            return None
        if float(rt) > 0.0 and int(p) == 0 and float(d) == 0.0:
            return self.make_issue("Çalışıp hiç üretmemek + duruş yok → şüpheli.")
        return None


class VC08Quality100WithScrap(Rule):
    id = "V-C08"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("quality", "scrap_qty")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        q = record.quality
        s = record.scrap_qty
        if q is None or s is None:
            return None
        if float(q) >= 100.0 and int(s) > 0:
            return self.make_issue("Q=100 ama fire>0 → çelişki.")  # %100 kalite + fire olmaz
        return None


class VC09Availability100WithUnplannedDown(Rule):
    id = "V-C09"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("availability", "unplanned_down")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        a = record.availability
        ud = record.unplanned_down
        if a is None or ud is None:
            return None
        if float(a) >= 100.0 and float(ud) > 0.0:
            return self.make_issue("A=100 ama plansız duruş>0 → çelişki.")
        return None


class VC10OeePositiveWithoutProduction(Rule):
    id = "V-C10"
    category = IssueCategory.CONSISTENCY
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("oee", "produced_qty")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        oee = record.oee
        p = record.produced_qty
        if oee is None or p is None:
            return None
        if float(oee) > 0.0 and int(p) == 0:
            return self.make_issue("Üretim=0 ama OEE>0 → sensör/log hatası olabilir.")
        return None


CONSISTENCY_RULES: tuple[Rule, ...] = (
    VC01ScrapGreaterThanProduced(),
    VC02OeeApxAPQ(),
    VC03QualityVsScrap(),
    VC04AvailabilityVsRunTime(),
    VC05DownTimeBreakdown(),
    VC06ProducedWithoutRunTime(),
    VC07RunWithoutProductionNoDown(),
    VC08Quality100WithScrap(),
    VC09Availability100WithUnplannedDown(),
    VC10OeePositiveWithoutProduction(),
)
