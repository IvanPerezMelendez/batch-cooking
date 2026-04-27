from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://batchcooking:batchcooking@localhost:5432/batchcooking"
    app_env: str = "local"

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"


settings = Settings()
