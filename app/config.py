from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/agenticleague"
    secret_key: str = "change-me-to-a-random-secret-key"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    api_rate_limit_per_minute: int = 60
    nba_api_delay_seconds: float = 2.0
    job_secret: str = ""  # Optional secret to protect job endpoints

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
