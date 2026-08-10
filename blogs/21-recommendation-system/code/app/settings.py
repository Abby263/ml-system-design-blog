from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    artifact_path: str = "artifacts/current/bundle.json"
    items_path: str = "data/items.csv"
    interactions_path: str = "data/interactions.csv"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
