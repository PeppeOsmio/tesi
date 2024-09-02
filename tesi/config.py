import logging
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    db_host: str = ""
    db_port: str = ""
    db_type: Literal["sqlite", "postgresql", "mariadb", "mysql"] = "sqlite"
    db_name: str = "tesi.db"
    db_user: str = ""
    db_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore
