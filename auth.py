"""OAuth2 token management for QuickBooks API."""
import time
from typing import Optional

import httpx

from config import settings


class TokenManager:
    """Manages OAuth tokens for QuickBooks API."""

    def __init__(self):
        """Initialize token manager with hardcoded tokens from config."""
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._expires_at: float = 0
        
        # Initialize with tokens from config
        self._load_tokens_from_config()

    def _load_tokens_from_config(self):
        """Load tokens from environment variables."""
        if settings.QB_ACCESS_TOKEN and settings.QB_REFRESH_TOKEN:
            # Set tokens (we don't know expiry, so set to expire soon to trigger refresh check)
            self._access_token = settings.QB_ACCESS_TOKEN
            self._refresh_token = settings.QB_REFRESH_TOKEN
            # Set expires_at to 0 to force refresh check on first use
            self._expires_at = 0

    def get_access_token(self) -> Optional[str]:
        """Get access token, refreshing if needed."""
        current_time = time.time()

        # Check if token needs refresh (or if we haven't validated it yet)
        if current_time >= self._expires_at:
            if not self._do_refresh_token():
                # If refresh fails, try using the hardcoded token as fallback
                return self._access_token

        return self._access_token

    def _do_refresh_token(self) -> bool:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            return False

        refresh_token_value = self._refresh_token
        try:
            response = httpx.post(
                settings.QB_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token_value,
                },
                auth=(settings.QB_CLIENT_ID, settings.QB_CLIENT_SECRET),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            # Update tokens
            self._access_token = data["access_token"]
            # Use new refresh token if provided, otherwise keep existing
            self._refresh_token = data.get("refresh_token", refresh_token_value)
            # Set expiry time (refresh 60 seconds before actual expiry)
            self._expires_at = time.time() + data["expires_in"] - 60

            return True
        except Exception:
            # Token refresh failed, but we can still try using the hardcoded token
            return False


# Global token manager instance
token_manager = TokenManager()

