from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "NEXORA"
    postgres_db: str = "nexora"
    postgres_user: str = "nexora"
    postgres_password: str = "troque_esta_senha"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "nexora"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 60
    outbox_poll_seconds: int = 2
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (f"postgresql+psycopg2://{self.postgres_user}:"
                f"{self.postgres_password}@{self.postgres_host}:"
                f"{self.postgres_port}/{self.postgres_db}")

settings = Settings()
