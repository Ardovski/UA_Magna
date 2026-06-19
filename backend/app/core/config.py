"""Uygulama ayarları — .env'den tip-güvenli okuma (pydantic-settings).

Secret'lar (TARGET_API_KEY) yalnız buradan erişilir; asla log'lanmaz, response'a konmaz.
Yollar CWD'den bağımsız mutlak hesaplanır (repo kökü = config.py parents[3]).
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py: <repo>/backend/app/core/config.py → parents[3] = <repo>.
_REPO_ROOT = Path(__file__).resolve().parents[3]
# Repo kökündeki db/ klasörü — veritabanının evi.
DB_DIR = _REPO_ROOT / "db"


class Settings(BaseSettings):
    """Tüm uygulama ayarları — .env'den okunur, eksikse buradaki varsayılan kullanılır."""

    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Uygulama ---
    app_env: str = "development"
    log_level: str = "INFO"

    # --- Veritabanı (SQLite) ---
    # Varsayılan: repo kökündeki db/app.db (mutlak yol → her CWD'den aynı dosya).
    database_url: str = f"sqlite:///{DB_DIR / 'app.db'}"

    # --- CORS ---
    cors_allow_origins: str = "http://localhost:3000"

    # --- Hedef (target) MES API ---
    target_api_url: str = "http://89.252.189.91:8983"
    target_api_submit_path: str = "/api/v1/submit"
    target_api_key: str = ""
    target_api_timeout_seconds: int = 15
    target_api_max_retries: int = 3
    target_api_backoff_base_seconds: int = 2
    target_api_rate_limit_cooldown_seconds: int = 60
    # Circuit breaker: ardışık N başarısız gönderimden sonra hedefe gönderimi
    # `cooldown` süresince otomatik duraklat (uzun süreli hata durumunda).
    sync_circuit_failure_threshold: int = 5
    sync_circuit_cooldown_seconds: int = 300

    # --- Validation eşik & toleranslar ---
    validation_tolerance_pct: float = 1.0
    validation_p_suspect_upper: float = 100.0
    validation_p_impossible_upper: float = 150.0
    validation_minutes_per_day: int = 1440
    validation_outlier_z_threshold: float = 3.0
    validation_systemic_ratio: float = 0.2
    validation_report_window_start: str = "2025-11-05"
    validation_report_window_end: str = "2025-11-25"
    validation_work_order_pattern: str = r"^302\d{7}$"
    validation_station_pattern: str = r"^IMM-\d+-\d+$"

    @property
    def cors_origins_list(self) -> list[str]:
        """Virgülle ayrılmış CORS origin string'ini temiz bir listeye çevirir."""
        # Boş parçaları at; baş/son boşlukları kırp (ör. "a, b" → ["a", "b"]).
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def target_submit_url(self) -> str:
        """Hedef MES API submit endpoint'inin tam URL'ini birleştirir."""
        # Çift slash olmaması için base URL'in sonundaki '/' temizlenir.
        return f"{self.target_api_url.rstrip('/')}{self.target_api_submit_path}"


settings = Settings()
