"""SQLAlchemy declarative Base + ortak kolon mixin'leri.

Tüm modeller `Base`'den türer. Tekrar eden kolonlar (id PK, created_at, updated_at)
buradaki mixin'lere çıkarıldı (DRY); modeller yalnız kendine özgü alanları tanımlar.

Şema DEĞİŞMEZ: kolon adı/tipi/server_default/onupdate birebir korunur — mixin yalnız
tanımı tek yere taşır. Mixin'ler `Mapped` attribute sağlar; mapping `Base` ile yapılır
(`class X(IntIdMixin, Base)`).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Ortak taban sınıf. Metadata buradan toplanır (create_all)."""


class IntIdMixin:
    """Otomatik artan tamsayı birincil anahtar (`id`)."""

    id: Mapped[int] = mapped_column(primary_key=True)


class CreatedAtMixin:
    """Oluşturulma zaman damgası (`created_at`, server_default=now)."""

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())


class UpdatedAtMixin:
    """Güncellenme zaman damgası (`updated_at`, now + onupdate)."""

    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
