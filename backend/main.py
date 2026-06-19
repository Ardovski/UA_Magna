"""Case 7.2 uyumluluk shim'i.

Case'in birebir komutu `cd backend && uvicorn main:app --reload` çalışsın diye
bu modül gerçek uygulamayı (app/main.py) yeniden export eder.

Önerilen çalıştırma yine de: `make dev` (api :8000 + web :3000 birlikte).
Bu dosya yalnızca "main:app" giriş noktasını bekleyen kopyala-yapıştır komutları içindir.
"""

from app.main import app

__all__ = ["app"]
