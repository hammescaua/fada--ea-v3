"""Configuração da API (variáveis de ambiente)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FADA_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://fada:fada@localhost:5432/fada"
    cors_origins: str = "http://localhost:3000"
    weather_provider: str = "open-meteo"  # open-meteo | nasa-power

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
