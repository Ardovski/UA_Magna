"""Sync feature paketi — yalnız status='valid' kayıtları (gün, vardiya) bazında
agrege edip hedef API'ye idempotent (idempotency_key + payload_hash) olarak gönderir.

Alt modüller:
  - aggregator: valid kayıtları (date, shift) gruplarına indirir, payload + hash üretir.
  - client    : hedef API'ye HTTP POST; X-Production-Key header'ı, secret redaction.
  - retry     : retry matrisi (429/5xx/ağ retry; 401/422/413 kalıcı) + backoff politikası.
  - service   : preview / submit / history / retry orkestrasyonu.
  - api       : FastAPI router; /submit 202 döner, gerçek gönderim BackgroundTasks ile.
"""
