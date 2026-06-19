"""Validation domain modelleri — Enum + Issue + record status türetme.

Bu modül kuralların ürettiği veri tiplerini tanımlar: kategori/severity/önerilen
aksiyon enum'ları, tekil `Issue` kaydı, kurallara çalışma-zamanı eşik/parametre
taşıyan `RuleContext` ve bir kaydın tüm issue'larını biriktirip statüsünü türeten
`ValidationResult`. Statü severity'den türer: ERROR→rejected, WARNING→suspect,
aksi halde valid.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum


# Kural kategorileri — 43 kural bu 6 grup altında toplanır.
class IssueCategory(StrEnum):
    MISSING = "missing"
    RANGE = "range"
    CONSISTENCY = "consistency"
    DUPLICATE = "duplicate"
    FORMAT = "format"
    DOMAIN = "domain"


# Ağırlık derecesi — kayıt statüsünü belirler (ERROR>WARNING>INFO).
class IssueSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Operatöre önerilen aksiyon — UI'da issue'ya göre rehberlik için.
class SuggestedAction(StrEnum):
    REJECT = "reject"
    WARN = "warn"
    FIX = "fix"


# Kayıt statüsü — severity'den türetilir; sadece valid kayıtlar hedef API'ye gider.
class RecordStatus(StrEnum):
    VALID = "valid"
    SUSPECT = "suspect"
    REJECTED = "rejected"


# Tek bir kural ihlali — immutable; bir kuralın tek bir kayıt için bulgusu.
@dataclass(frozen=True)
class Issue:
    rule_id: str
    category: IssueCategory
    severity: IssueSeverity
    fields: tuple[str, ...]
    message: str
    suggested_action: SuggestedAction


# Kurallara çalışma-zamanı eşik/parametre taşıyan bağlam (settings'ten doldurulur).
# Batch-pass için dinamik alanlar (row_hash_seen vb.) motorda sonradan eklenir.
@dataclass
class RuleContext:
    tolerance_pct: float
    p_suspect_upper: float
    p_impossible_upper: float
    minutes_per_day: int
    outlier_z_threshold: float
    work_order_pattern: str
    station_pattern: str
    window_start: str
    window_end: str


# Bir kaydın tüm issue'larını biriktirir; statüyü bunlardan türetir.
@dataclass
class ValidationResult:
    record_id: int
    issues: list[Issue] = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)

    def extend(self, issues: Sequence[Issue]) -> None:
        self.issues.extend(issues)

    @property
    def has_error(self) -> bool:
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warning(self) -> bool:
        return any(i.severity == IssueSeverity.WARNING for i in self.issues)

    @property
    def status(self) -> RecordStatus:
        # Statü türetimi (öncelik sırasıyla): tek bir ERROR varsa kayıt reddedilir;
        # ERROR yok ama WARNING varsa şüpheli; hiçbiri yoksa geçerli. INFO statüyü
        # etkilemez. Sadece "valid" kayıtlar hedef API'ye gönderilmeye uygundur.
        if self.has_error:
            return RecordStatus.REJECTED
        if self.has_warning:
            return RecordStatus.SUSPECT
        return RecordStatus.VALID
