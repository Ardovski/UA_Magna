"""Records CSV export — streaming, UTF-8 BOM, filtreyi yansıtır."""

from __future__ import annotations

import csv
import datetime as dt
import io
from collections.abc import Iterable, Iterator
from typing import Any

from app.features.records.schemas import RecordFilter

# CSV başlık sırası: Türkçe başlıklar (kullanıcıya gösterilen), domain CSV'siyle uyumlu.
_COLUMNS: tuple[str, ...] = (
    "record_id",
    "Tarih",
    "İş Emri No",
    "İş Merkezi No",
    "İşmerkezi Adı",
    "İş İstasyon Adı",
    "Stok Adı",
    "Vardiya",
    "A (Kullanılırlık)",
    "P (Performans)",
    "Q (Kalite)",
    "OEE",
    "Çalışma Süresi",
    "Duruş Süresi",
    "Planlı Duruş Süresi",
    "Plansız Duruş Süresi",
    "Üretilen Miktar",
    "Hatalı Üretilen Miktar",
    "validation_status",
    "issue_count",
)

# Türkçe CSV başlığı -> model attribute eşlemesi. "issue_count" burada yok;
# o değer kayıt değil, issue alt-sorgusundan ayrıca gelir (rows_to_csv_lines).
_FIELD_MAP: dict[str, str] = {
    "record_id": "record_id_src",
    "Tarih": "prod_date",
    "İş Emri No": "work_order_no",
    "İş Merkezi No": "work_center_no",
    "İşmerkezi Adı": "work_center_name",
    "İş İstasyon Adı": "station_name",
    "Stok Adı": "stock_name",
    "Vardiya": "shift",
    "A (Kullanılırlık)": "availability",
    "P (Performans)": "performance",
    "Q (Kalite)": "quality",
    "OEE": "oee",
    "Çalışma Süresi": "run_time",
    "Duruş Süresi": "down_time",
    "Planlı Duruş Süresi": "planned_down",
    "Plansız Duruş Süresi": "unplanned_down",
    "Üretilen Miktar": "produced_qty",
    "Hatalı Üretilen Miktar": "scrap_qty",
    "validation_status": "status",
}


def _format_cell(value: Any) -> str:
    """Bir hücre değerini CSV metnine çevirir: None -> boş, tarih/saat -> ISO,
    float -> gereksiz sıfırlar kırpılır."""
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, float):
        # 4 ondalık basamağa yuvarla, sondaki sıfırları ve gereksiz noktayı temizle.
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def rows_to_csv_lines(rows: Iterable[Any]) -> Iterator[str]:
    """(model, issue_count) satırlarını CSV metin parçalarına çevirerek tembel (lazy) akıtır.

    Önce başlık satırı, sonra her kayıt için bir satır yield edilir. Tek satırlık
    bir StringIO tampon her satırdan sonra sıfırlanır; böylece tüm dosya belleğe
    alınmadan büyük export'lar stream'lenir.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=",", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    # Başlık satırını yaz ve hemen yield et.
    writer.writerow(_COLUMNS)
    yield buf.getvalue()
    # Tamponu sonraki satır için sıfırla.
    buf.seek(0)
    buf.truncate(0)

    for row in rows:
        # Her satır: [0] ProductionRecord modeli, [1] issue alt-sorgusundan kayıt sorun sayısı.
        model = row[0]
        issue_count = int(row[1] or 0)
        out: list[str] = []
        for col in _COLUMNS:
            # issue_count modelde olmadığından ayrıca işlenir.
            if col == "issue_count":
                out.append(str(issue_count))
                continue
            # Başlığı model attribute'una eşle (eşleme yoksa başlığın kendisi kullanılır).
            attr = _FIELD_MAP.get(col, col)
            out.append(_format_cell(getattr(model, attr, None)))
        writer.writerow(out)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)


def csv_filename(prefix: str = "records") -> str:
    """İndirme için zaman damgalı dosya adı üretir, örn. `records_20251119_143005.csv`."""
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}.csv"


def filter_to_query_dict(flt: RecordFilter) -> dict[str, Any]:
    """`RecordFilter`'ı JSON-serileştirilebilir düz dict'e çevirir (tarihler ISO string'e döner)."""
    return {
        "prod_date_range": (
            {
                "start": flt.prod_date_range.start.isoformat()
                if flt.prod_date_range and flt.prod_date_range.start
                else None,
                "end": flt.prod_date_range.end.isoformat()
                if flt.prod_date_range and flt.prod_date_range.end
                else None,
            }
            if flt.prod_date_range
            else None
        ),
        "shift": list(flt.shift),
        "station_name": list(flt.station_name),
        "stock_name": flt.stock_name,
        "oee_range": (
            {"min": flt.oee_range.min, "max": flt.oee_range.max} if flt.oee_range else None
        ),
        "validation_status": list(flt.validation_status),
        "has_issues": flt.has_issues,
    }
