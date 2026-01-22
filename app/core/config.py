import os
from typing import Optional
from datetime import timedelta


class Settings:
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = os.getenv("APP_NAME", "fastapi-ldap-ad")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # LDAP/AD Configuration (optional for testing)
    ldap_server: Optional[str] = os.getenv("LDAP_SERVER")
    ldap_port: int = int(os.getenv("LDAP_PORT", "389"))
    ldap_use_ssl: bool = os.getenv("LDAP_USE_SSL", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    ldap_bind_dn: Optional[str] = os.getenv("LDAP_BIND_DN")
    ldap_bind_password: Optional[str] = os.getenv("LDAP_BIND_PASSWORD")
    ldap_base_dn: Optional[str] = os.getenv("LDAP_BASE_DN")

    # JWT Configuration
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Audit Logging
    audit_log_path: str = os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl")

    @classmethod
    def get_jwt_expiration(cls) -> timedelta:
        """Get JWT token expiration time."""
        return timedelta(hours=cls.jwt_expiration_hours)


settings = Settings()
