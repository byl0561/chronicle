from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHRONICLE_", env_file=".env", extra="ignore")

    data_dir: str = "./data"
    db_filename: str = "chronicle.db"
    cors_origins: str = "*"

    @property
    def database_url(self) -> str:
        db_path = Path(self.data_dir) / self.db_filename
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
