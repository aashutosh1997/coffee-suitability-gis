from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://terrabean:change-me-locally@localhost:5432/terrabean"
    )
    redis_url: str = "redis://localhost:6379/0"

    # NFR-14: the suitability model is version-controlled config, loaded at runtime.
    suitability_config_path: str = "/config/suitability/arabica-2026.1.yaml"

    minio_endpoint: str = "http://localhost:9000"
    minio_bucket: str = "terrabean-cogs"

    # Phase 0 runs without Keycloak; auth bypass must be false once SSO lands (Phase 4).
    dev_auth_bypass: bool = True

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
