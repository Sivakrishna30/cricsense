from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CricSense Backend"
    base_dir: Path = Path(__file__).resolve().parent.parent
    source_db_path: Path = Field(default=Path("cricsense.db"))
    analytics_db_path: Path = Field(default=Path("cricsense_analytics.db"))
    cricapi_key: str = Field(default="")
    cricapi_base_url: str = Field(default="https://api.cricapi.com/v1")
    live_cache_ttl_seconds: int = Field(default=900)


settings = Settings()
