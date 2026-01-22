from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="fastapi-ldap-ad", validation_alias="APP_NAME")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=True, validation_alias="DEBUG")

    # LDAP/AD Configuration (optional for testing)
    ldap_server: Optional[str] = Field(default=None, validation_alias="LDAP_SERVER")
    ldap_port: int = Field(default=389, validation_alias="LDAP_PORT")
    ldap_use_ssl: bool = Field(default=False, validation_alias="LDAP_USE_SSL")
    ldap_bind_dn: Optional[str] = Field(default=None, validation_alias="LDAP_BIND_DN")
    ldap_bind_password: Optional[str] = Field(
        default=None, validation_alias="LDAP_BIND_PASSWORD"
    )
    ldap_base_dn: Optional[str] = Field(default=None, validation_alias="LDAP_BASE_DN")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
