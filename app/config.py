import os
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
      env_file=".env", env_file_encoding="utf-8", extra="ignore"
  )

  postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
  postgres_password: str = os.getenv(
      "POSTGRES_PASSWORD", "your_password"
  )  # No real password here
  postgres_db: str = os.getenv("POSTGRES_DB", "url_shortener_db")
  postgres_host: str = os.getenv("POSTGRES_HOST", "db")
  postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))

  database_url: str = ""
  redis_host: str = os.getenv("REDIS_HOST", "redis")
  redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
  redis_url: str = ""
  redis_cache_ttl_seconds: int = 86400
  base_url: str = os.getenv("BASE_URL", "http://localhost:8000")

  def model_post_init(self, __context):
    safe_password = quote_plus(self.postgres_password)
    self.database_url = f"postgresql+psycopg2://{self.postgres_user}:{safe_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    if not self.redis_url or "REDIS_HOST" in self.redis_url:
      self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()