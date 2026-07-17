from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    DATABASE_URL: str  # Формат: postgresql://user:password@host:port/dbname

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Settings()