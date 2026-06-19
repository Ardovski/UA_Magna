"""Duplicate kuralları (V-D01..D04) — satır içi bilgi taşıyıcı + batch hook.

İçerik/iş-anahtarı/dosya düzeyinde tekrar tespiti: V-D01 aynı satır (row_hash)
tekrarı, V-D02 iş anahtarı çakışması (batch-pass), V-D03 aynı MES kayıt id'si,
V-D04 daha önce import edilmiş CSV dosyası. İlk ikisi ERROR (reddedilir); son
ikisi WARNING (şüpheli — operatör kararı).
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


class VD01RowHashDuplicate(Rule):
    id = "V-D01"
    category = IssueCategory.DUPLICATE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("row_hash",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        seen: set[str] | None = getattr(ctx, "row_hash_seen", None)
        if seen is None:
            return None
        rh = getattr(record, "row_hash", None)
        if rh and rh in seen:
            return self.make_issue(
                "Aynı satır (row_hash) daha önce import edilmiş."
            )  # aynı içerik → reddedilir
        if rh:
            seen.add(rh)
        return None


class VD02BusinessKeyConflict(Rule):
    id = "V-D02"
    category = IssueCategory.DUPLICATE
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("prod_date", "shift", "station_name", "work_order_no")

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        return None


class VD03RecordIdDuplicate(Rule):
    id = "V-D03"
    category = IssueCategory.DUPLICATE
    severity = IssueSeverity.ERROR
    action = SuggestedAction.REJECT
    fields = ("record_id",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        seen: dict[int, int] | None = getattr(ctx, "record_id_seen", None)
        if seen is None:
            return None
        rid = getattr(record, "record_id_src", None)
        if rid is None:
            return None
        if int(rid) in seen:
            return self.make_issue(
                f"record_id={rid} başka bir satırda da kullanılmış."
            )  # MES id çakışması
        seen[int(rid)] = int(rid)
        return None


class VD04FileHashDuplicate(Rule):
    id = "V-D04"
    category = IssueCategory.DUPLICATE
    severity = IssueSeverity.WARNING
    action = SuggestedAction.WARN
    fields = ("file_hash",)

    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        fhash = getattr(ctx, "current_file_hash", None)
        seen_files: set[str] | None = getattr(ctx, "file_hash_seen", None)
        if not fhash or seen_files is None:
            return None
        if fhash in seen_files:
            return self.make_issue(
                "Bu CSV daha önce import edilmiş (file_hash)."
            )  # dosya tekrarı (uyarı)
        seen_files.add(fhash)
        return None


DUPLICATE_RULES: tuple[Rule, ...] = (
    VD01RowHashDuplicate(),
    VD02BusinessKeyConflict(),
    VD03RecordIdDuplicate(),
    VD04FileHashDuplicate(),
)
