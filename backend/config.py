from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/rulelawyerdb"
    RULES_FILE_URL: str = "https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.txt"

    VOYAGE_API_KEY: str = ""
    EMBEDDING_MODEL: str = "voyage-3-lite"
    VECTOR_SEARCH_LIMIT: int = 5

    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    MAX_TOKENS: int = 1000

    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def async_database_url(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
