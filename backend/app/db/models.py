"""SQLAlchemy modelleri — 6 tablo.

Şema dokümantasyonu (kaynak doğruluk): .docs/api/database.md
İsimlendirme: tablo snake_case çoğul, kolon snake_case (bkz. .docs/shared/conventions/naming.md).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, IntIdMixin, UpdatedAtMixin


class ImportBatch(IntIdMixin, Base):
    """Her CSV yükleme bir batch. file_hash → aynı dosya duplicate tespiti."""

    __tablename__ = "import_batches"

    filename: Mapped[str] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)
    suspect_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # status: processing|completed|failed|duplicate
    status: Mapped[str] = mapped_column(String(20), default="processing")

    records: Mapped[list[ProductionRecord]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class ProductionRecord(IntIdMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """Ana üretim kaydı — 18 kaynak kolon + türetilmiş/meta alanlar."""

    __tablename__ = "production_records"
    __table_args__ = (
        UniqueConstraint("row_hash", name="uq_record_row_hash"),
        Index("ix_record_date_shift_station", "prod_date", "shift", "station_name"),
    )

    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))
    record_id_src: Mapped[int | None] = mapped_column(Integer, index=True)

    # boyutlar
    prod_date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    work_order_no: Mapped[str | None] = mapped_column(String(20))
    work_center_no: Mapped[str | None] = mapped_column(String(50))
    work_center_name: Mapped[str | None] = mapped_column(String(120))
    station_name: Mapped[str | None] = mapped_column(String(60), index=True)
    stock_name: Mapped[str | None] = mapped_column(String(120))
    shift: Mapped[int | None] = mapped_column(Integer, index=True)

    # OEE bileşenleri + metrikler
    availability: Mapped[float | None] = mapped_column(Float)
    performance: Mapped[float | None] = mapped_column(Float)
    quality: Mapped[float | None] = mapped_column(Float)
    oee: Mapped[float | None] = mapped_column(Float)
    run_time: Mapped[float | None] = mapped_column(Float)
    down_time: Mapped[float | None] = mapped_column(Float)
    planned_down: Mapped[float | None] = mapped_column(Float)
    unplanned_down: Mapped[float | None] = mapped_column(Float)
    produced_qty: Mapped[int | None] = mapped_column(Integer)
    scrap_qty: Mapped[int | None] = mapped_column(Integer)

    # türetilmiş + meta
    oee_recomputed: Mapped[float | None] = mapped_column(Float)
    row_hash: Mapped[str] = mapped_column(String(64))
    # status: valid|suspect|rejected|fixed
    status: Mapped[str] = mapped_column(String(20), default="valid", index=True)
    # id, created_at, updated_at → IntIdMixin / CreatedAtMixin / UpdatedAtMixin

    batch: Mapped[ImportBatch | None] = relationship(back_populates="records")
    issues: Mapped[list[ValidationIssue]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )
    edits: Mapped[list[RecordEdit]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )


class ValidationIssue(IntIdMixin, CreatedAtMixin, Base):
    """Kayıt başına 0..N validasyon bulgusu (kural kataloğuna referans)."""

    __tablename__ = "validation_issues"

    record_id: Mapped[int] = mapped_column(ForeignKey("production_records.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String(10))  # örn. V-C01
    # category: missing|range|consistency|duplicate|format|domain
    category: Mapped[str] = mapped_column(String(20))
    severity: Mapped[str] = mapped_column(String(10))  # error|warning|info
    field_names: Mapped[str | None] = mapped_column(Text)  # etkilenen alan(lar), JSON/CSV
    message: Mapped[str] = mapped_column(Text)
    suggested_action: Mapped[str] = mapped_column(String(10))  # reject|warn|fix
    # status: open|fixed|rejected|accepted
    status: Mapped[str] = mapped_column(String(12), default="open")

    record: Mapped[ProductionRecord] = relationship(back_populates="issues")


class RecordEdit(IntIdMixin, Base):
    """Manuel düzeltme audit trail'i (bonus)."""

    __tablename__ = "record_edits"

    record_id: Mapped[int] = mapped_column(ForeignKey("production_records.id"), index=True)
    field: Mapped[str] = mapped_column(String(40))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    edited_by: Mapped[str] = mapped_column(String(60), default="operator")
    edited_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    record: Mapped[ProductionRecord] = relationship(back_populates="edits")


class SyncSubmission(IntIdMixin, CreatedAtMixin, Base):
    """Hedef API gönderim log'u — idempotency + retry takibi."""

    __tablename__ = "sync_submissions"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_sync_idempotency_key"),)

    prod_date: Mapped[dt.date] = mapped_column(Date, index=True)
    shift: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(40))  # "{prod_date}:{shift}"
    payload_hash: Mapped[str] = mapped_column(String(64))
    # status: pending|success|failed|retrying
    status: Mapped[str] = mapped_column(String(12), default="pending")
    http_status: Mapped[int | None] = mapped_column(Integer)
    target_submission_id: Mapped[int | None] = mapped_column(Integer)
    # Hedef API'nin başarılı yanıtından (case §5.5: success, submission_id, candidate_name,
    # message, submitted_at) yakalanan ek alanlar — operatörün gönderim sonucunu görmesi için.
    target_candidate_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_submitted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    # created_at → CreatedAtMixin


class AppSetting(UpdatedAtMixin, Base):
    """Anahtar-değer uygulama ayarları (key='active_batch_id' vb.)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    # updated_at → UpdatedAtMixin
