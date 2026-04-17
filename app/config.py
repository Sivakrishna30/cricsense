from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CricSense Backend"
    base_dir: Path = Path(__file__).resolve().parent.parent
    source_db_path: Path = Field(default=Path("cricsense.db"))
    analytics_db_path: Path = Field(default=Path("cricsense_analytics.db"))
    auth_db_path: Path = Field(default=Path("cricsense_auth.db"))
    cricapi_key: str = Field(default="")
    cricapi_base_url: str = Field(default="https://api.cricapi.com/v1")
    live_cache_ttl_seconds: int = Field(default=900)
    ipl_series_id: str = Field(default="")
    matchday_cache_path: Path = Field(default=Path("matchday_cache.json"))
    matchday_schedule_ttl_seconds: int = Field(default=43200)
    matchday_info_ttl_seconds: int = Field(default=900)
    matchday_squad_ttl_seconds: int = Field(default=900)
    squad_refresh_lead_minutes: int = Field(default=15)
    weather_cache_ttl_seconds: int = Field(default=21600)
    weather_geocode_url: str = Field(default="https://geocoding-api.open-meteo.com/v1/search")
    weather_forecast_url: str = Field(default="https://api.open-meteo.com/v1/forecast")
    app_session_secret: str = Field(default="")
    app_access_token_minutes: int = Field(default=60)
    app_refresh_token_days: int = Field(default=30)
    google_android_client_id: str = Field(default="")
    apple_ios_audience: str = Field(default="")


settings = Settings()
