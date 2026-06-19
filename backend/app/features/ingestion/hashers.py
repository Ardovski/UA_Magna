"""Hashleme yardımcıları — file_hash (SHA-256) + row_hash (kanonik JSON)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def file_hash_from_bytes(data: bytes) -> str:
    """Dosyanın ham byte'larından SHA-256 üretir → dosya bazlı dedupe (duplicate file) için."""
    return hashlib.sha256(data).hexdigest()


def row_hash_from_mapping(row: Mapping[str, Any]) -> str:
    """Tek bir satırdan kanonik (deterministik) hash üretir → satır bazlı
    dedupe (duplicate row) için.

    Aynı içerikli satırın daima aynı hash'i vermesi için anahtarlar sıralanır ve
    JSON serileştirme sabit ayarlarla yapılır.
    """
    # Anahtarları alfabetik sırala + row_hash alanını dışla (kendini hash'e dahil etmemek için);
    # böylece kolon sırası/whitespace farkı olsa bile aynı veri aynı hash'i üretir.
    canonical = json.dumps(
        {k: row.get(k) for k in sorted(row.keys()) if k != "row_hash"},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
