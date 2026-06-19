"""Sync Pydantic şemaları — preview/submit istek ve yanıt modelleri ile gönderim çıktıları.

İçerik: hedef API payload'ı (SyncPayload), önizleme grupları (SyncGroupPreview/SyncPreview),
submission kayıt çıktısı (SubmissionOut) ve submit istek/yanıt modelleri.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class SyncPayload(BaseModel):
    """Hedef API'ye (gün, vardiya) bazında gönderilen agrege üretim payload'ı."""

    production_date: dt.date
    shift: int
    machine_count: int
    total_production_units: int
    oe_value: float


class SyncGroupPreview(BaseModel):
    """Önizlemede tek bir grup: payload alanları + idempotency_key/payload_hash +
    kaynak kayıt sayısı + hedef API uyumluluk durumu."""

    production_date: dt.date
    shift: int
    machine_count: int
    total_production_units: int
    oe_value: float | None = None
    idempotency_key: str
    payload_hash: str
    source_record_count: int
    # Hedef API constraint'lerine (case §5.5) uygunluk — uyumsuzsa grup gönderilmez,
    # UI badge ile gösterilir ve /submit sonucunda `rejected_target_constraints` listesinde döner.
    target_valid: bool = True
    target_issues: list[str] = Field(default_factory=list)


class SyncPreview(BaseModel):
    """Gönderilebilecek tüm grupların önizleme yanıtı (gruplar + toplam sayı)."""

    groups: list[SyncGroupPreview]
    total_groups: int
    # Uyumlu olmayan grup sayısı — UI banner'da özet olarak gösterilir.
    not_target_compliant_count: int = 0


class SubmissionOut(BaseModel):
    """Bir SyncSubmission DB kaydının API çıktısı: durum, http_status, deneme sayısı, hata vb."""

    id: int
    prod_date: dt.date
    shift: int
    idempotency_key: str
    payload_hash: str
    status: str
    http_status: int | None = None
    target_submission_id: int | None = None
    attempts: int
    last_attempt_at: dt.datetime | None = None
    created_at: dt.datetime | None = None
    error_message: str | None = None
    response_body: str | None = None


class SubmitTarget(BaseModel):
    """UI'da seçilen tek bir (gün, vardiya) grubu. `SubmitRequest.targets` listesinin elemanı."""

    production_date: dt.date
    shift: int


class SubmitRequest(BaseModel):
    """/submit isteği. force=True ise success olmuş gruplar payload_hash çakışmasına rağmen
    yeniden gönderilir."""

    production_date: dt.date | None = None
    shift: int | None = None
    # Birden çok (gün, vardiya) seçimi için: doluysa yalnız bu grup(lar) gönderilir.
    # Boş/None ise tek (production_date, shift) ya da (ikisi de yoksa) tüm gruplar.
    targets: list[SubmitTarget] | None = None
    force: bool = Field(default=False)


class SubmitResponse(BaseModel):
    """/submit yanıtı: kabul edilen, atlanan (zaten success), hash çakışması veya
    hedef API constraint ihlali nedeniyle reddedilen idempotency_key'ler + arka planda
    işlenecek submission_id'ler.
    """

    # `accepted` idempotency_key (örn. "2025-11-05:1") tutar → str. Eskiden yanlışlıkla
    # list[int] idi; "2025-11-05:1" int'e cast edilemediği için yanıt serileştirme hatası
    # riski vardı (frontend tipi de string[]).
    accepted: list[str] = Field(default_factory=list)
    skipped_already_success: list[str] = Field(default_factory=list)
    rejected_due_to_hash_conflict: list[str] = Field(default_factory=list)
    # Hedef API kabul etmediği için (oe_value/machine_count/total_units aralık dışı,
    # gelecek tarih vb.) gönderilmeyen gruplar — payload hiç oluşturulmaz.
    rejected_target_constraints: list[str] = Field(default_factory=list)
    submission_ids: list[int] = Field(default_factory=list)
