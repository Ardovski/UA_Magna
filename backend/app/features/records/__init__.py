"""Records feature — paginated liste + CSV export.

7'li filtre setini (tarih/vardiya/istasyon/stok/OEE/statü/sorun) SQL WHERE'ye
çevirir; sıralama + sayfalama destekler; tüm sonuç kümesini CSV olarak akıtarak
indirir (UTF-8 BOM, streaming — 100K+ satır için uygun).
"""
