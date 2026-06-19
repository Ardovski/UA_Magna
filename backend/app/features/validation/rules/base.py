"""Rule taban sınıfı — tüm kurallar bundan türer.

Her kural, sınıf düzeyinde sabit bir kimlik taşır: `id` (V-M01 gibi), `category`,
`severity`, önerilen `action` ve ilgili `fields`. `check()` tek kaydı denetler ve
ihlal varsa `Issue` döner, yoksa None. Severity'den kayıt statüsü türetilir
(ERROR→rejected, WARNING→suspect, aksi halde valid).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from app.features.validation.models import (
    Issue,
    IssueCategory,
    IssueSeverity,
    RuleContext,
    SuggestedAction,
)


class Rule(ABC):
    id: str = ""
    category: IssueCategory = IssueCategory.MISSING
    severity: IssueSeverity = IssueSeverity.WARNING
    action: SuggestedAction = SuggestedAction.WARN
    fields: tuple[str, ...] = ()

    @abstractmethod
    def check(self, record: Any, ctx: RuleContext) -> Issue | None:
        # Tek kaydı denetler; ihlal varsa Issue döner, temizse None.
        ...

    def make_issue(self, message: str) -> Issue:
        # Sınıf düzeyindeki sabit metadata'yı (id/category/severity/fields/action)
        # verilen mesajla birleştirip Issue üretir — kural koduna tekrar yazmamak için.
        return Issue(
            rule_id=self.id,
            category=self.category,
            severity=self.severity,
            fields=self.fields,
            message=message,
            suggested_action=self.action,
        )


class CompositeRule(Rule):
    # Birden çok kuralı tek kural gibi sarmalar; check() hepsini sırayla çalıştırıp
    # toplanan Issue listesini döner (hiç ihlal yoksa None).
    def __init__(self, rules: Sequence[Rule]) -> None:
        self._rules: list[Rule] = list(rules)

    @property
    def id(self) -> str:  # type: ignore[override]
        return "+".join(r.id for r in self._rules)

    def check(self, record: Any, ctx: RuleContext) -> list[Issue] | None:
        out: list[Issue] = []
        for r in self._rules:
            res = r.check(record, ctx)
            if res is None:
                continue
            if isinstance(res, list):
                out.extend(res)
            else:
                out.append(res)
        return out or None
