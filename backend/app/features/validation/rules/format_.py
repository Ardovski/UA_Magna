"""Format tutarsızlık kuralları (V-F01..F06).

Veri format normalize edildikten sonra eski/yeni arasındaki farkı raporlar: ISO
dışı tarih, virgül ondalık ayracı, 0-1'den 0-100'e ölçeklenen yüzde, iş emri/
istasyon desenleri dışı değer, trim+lower uygulanan string alanlar. Çoğu INFO
(operatöre bilgi), V-F03/V-F04 ise WARNING (şüpheli).
"""

from __future__ import annotations

import re
from typing import Any

from app.features.validation.models import (
    Issue,
    IssueCategory,
    IssueSeverity,
    RuleContext,
    SuggestedAction,
)
from app.features.validation.rules.base import Rule


class VF01DateFormatMixed(Rule):
    id = "V-F01"
    category = IssueCategory.FORMAT
    severity = IssueSeverity.INFO
    action = SuggestedAction.FIX
    fields = ("prod_date",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        raw = getattr(record, "_raw_prod_date", None)
        if raw is None or not isinstance(raw, str):
            return None
        text = raw.strip()
        if not text:
            return None
        iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}$", text))  # ISO-8601 (YYYY-MM-DD) beklentisi
        if iso:
            return None
        if record.prod_date is None:
            return None
        return self.make_issue(
            f"Tarih formatı '{text}' ISO değil; normalize edildi → {record.prod_date.isoformat()}."
        )


class VF02DecimalComma(Rule):
    id = "V-F02"
    category = IssueCategory.FORMAT
    severity = IssueSeverity.INFO
    action = SuggestedAction.FIX
    fields = ("availability", "performance", "quality", "oee", "run_time", "down_time")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        for n in (
            "availability",
            "performance",
            "quality",
            "oee",
            "run_time",
            "down_time",
        ):
            raw = getattr(record, f"_raw_{n}", None)
            if isinstance(raw, str) and "," in raw:
                # Türkçe locale'de ondalık ayracı virgül olur;
                # sisteme nokta olarak girmesi beklenir.
                return self.make_issue(
                    f"Ondalık ayraç virgül ({n}='{raw}') → noktaya normalize edildi."
                )
        return None


class VF03PercentScaleInUnit(Rule):
    id = "V-F03"
    category = IssueCategory.FORMAT
    severity = IssueSeverity.WARNING
    action = SuggestedAction.FIX
    fields = ("availability", "performance", "quality", "oee")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        scaled = getattr(
            record, "_pct_rescaled", None
        )  # normalize adımı ölçek değişikliği yaptıysa işaretlenir
        if not scaled:
            return None
        return self.make_issue("A/P/Q değerleri 0-1 ölçeğinde → 0-100'e ölçeklendi.")


class VF04WorkOrderPattern(Rule):
    id = "V-F04"
    category = IssueCategory.FORMAT
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("work_order_no",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.work_order_no
        if v is None or v == "":
            return None
        if not re.match(ctx.work_order_pattern, v):
            return self.make_issue(
                f"work_order_no='{v}' beklenen desen dışında ({ctx.work_order_pattern})."
            )
        return None


class VF05StringTrimCase(Rule):
    id = "V-F05"
    category = IssueCategory.FORMAT
    severity = IssueSeverity.INFO
    action = SuggestedAction.FIX
    fields = ("station_name", "stock_name", "work_center_name")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        for n in ("station_name", "stock_name", "work_center_name"):
            raw = getattr(record, f"_raw_{n}", None)
            cur = getattr(record, n, None)
            if (
                isinstance(raw, str)
                and cur is not None
                and (raw != cur or raw != raw.strip() or raw != raw.lower())
            ):
                # Herhangi bir normalizasyon (trim/lower/düzeltme) olduysa INFO issue üret.
                return self.make_issue(f"{n}='{raw}' trim+lower normalize uygulandı → '{cur}'.")
        return None


class VF06StationPattern(Rule):
    id = "V-F06"
    category = IssueCategory.FORMAT
    severity = IssueSeverity.INFO
    action = SuggestedAction.WARN
    fields = ("station_name",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        v = record.station_name
        if v is None or v == "":
            return None
        if not re.match(ctx.station_pattern, v):
            return self.make_issue(f"station_name='{v}' beklenen IMM-####-# desenine uymuyor.")
        return None


FORMAT_RULES: tuple[Rule, ...] = (
    VF01DateFormatMixed(),
    VF02DecimalComma(),
    VF03PercentScaleInUnit(),
    VF04WorkOrderPattern(),
    VF05StringTrimCase(),
    VF06StationPattern(),
)
