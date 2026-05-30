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
    minio_root_user: str = "terrabean"
    minio_root_password: str = "change-me-locally"

    # TiTiler base URL used by the /overlays endpoint to build raster tile URLs the
    # browser fetches directly (FR-13). Dev: docker-compose `titiler` on :8001;
    # production fronts both api and titiler behind nginx so this becomes a path.
    titiler_base_url: str = "http://localhost:8001"

    # Dataset names the engine resolves against dataset_provenance (FR-15). DEM is
    # terrain; the three climate datasets arrive in Phase 2 (ADR-0007).
    dem_dataset_name: str = "copernicus-glo30"
    temperature_dataset_name: str = "chelsa-tas-annual"
    precip_annual_dataset_name: str = "chelsa-pr-annual"
    precip_monthly_dataset_name: str = "chelsa-pr-monthly"
    # When set, cog_reader reads this local COG instead of MinIO + PostGIS provenance.
    # Used by tests and offline dev so geoprocessing runs without the stack.
    cog_local_dir: str | None = None

    # Phase 0 runs without Keycloak; auth bypass must be false once SSO lands (Phase 4).
    dev_auth_bypass: bool = True

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
