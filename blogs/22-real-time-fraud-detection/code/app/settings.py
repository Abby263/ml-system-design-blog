from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    artifact_path: str = "artifacts/current/model.json"
    database_path: str = "fraud.db"
    training_data_path: str = "data/transactions.csv"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
