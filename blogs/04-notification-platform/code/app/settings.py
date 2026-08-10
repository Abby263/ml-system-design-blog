from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_path: str = "notifications.db"
    callback_secret: str = "local-development-secret"
    job_lease_seconds: int = 30
    max_attempts: int = 5
    retry_base_seconds: float = 1.0
    retry_max_seconds: float = 60.0
    worker_poll_seconds: float = 0.5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
