"""Configuration management for QuickBooks Proxy API."""
import secrets
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # QuickBooks OAuth2 Credentials
    QB_CLIENT_ID: str
    QB_CLIENT_SECRET: str

    # QuickBooks Account Credentials (hardcoded)
    QB_ACCESS_TOKEN: str
    QB_REFRESH_TOKEN: str
    QB_REALM_ID: str  # Company ID / Realm ID

    # QuickBooks Environment
    QB_ENVIRONMENT: Literal["sandbox", "production"] = "sandbox"

    # OAuth2 URLs (for token refresh)
    QB_TOKEN_URL: str = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    # Proxy Configuration
    PROXY_PORT: int = 8000
    PROXY_BEARER_TOKEN: str = ""  # Bearer token for proxy API authentication

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def qb_base_url(self) -> str:
        """Get QuickBooks API base URL based on environment."""
        if self.QB_ENVIRONMENT == "sandbox":
            return "https://sandbox-quickbooks.api.intuit.com"
        return "https://quickbooks.api.intuit.com"



# Global settings instance
settings = Settings()

