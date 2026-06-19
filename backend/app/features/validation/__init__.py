"""Validation feature — veri kalite validasyon motoru + raporlama.

Bu paket, MES'ten import edilen üretim kayıtlarını 6 kategori altında toplam 43
kuralla denetler (missing/range/consistency/duplicate/format/domain). Motor iki
geçişlidir: PASS 1 her kayda saf kuralları uygular, PASS 2 batch düzeyinde iş
anahtarı çakışması (V-D02) ve istatistiksel outlier (V-X05) tespiti yapar.
Issue'lar kalıcı yazılmaz; her çağrıda canlı üretilir.
"""
