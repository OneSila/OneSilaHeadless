"""Utility mixins for eBay API access."""

from __future__ import annotations

import requests
from ebay_rest.reference import Reference

from .models.sales_channels import EbaySalesChannel


class GetEbayAPIMixin:
    """Mixin providing a simple authenticated requests session for eBay."""

    api: requests.Session
    api_host: str
    identity_host: str

    def get_api(self) -> requests.Session:
        """Return an authenticated :class:`requests.Session` for eBay APIs."""

        host = "https://api.ebay.com"
        identity_host = "https://apiz.ebay.com"
        if getattr(self.sales_channel, "environment", EbaySalesChannel.PRODUCTION) == EbaySalesChannel.SANDBOX:
            host = "https://api.sandbox.ebay.com"
            identity_host = "https://apiz.sandbox.ebay.com"

        session = requests.Session()
        if getattr(self.sales_channel, "access_token", None):
            session.headers.update({"Authorization": f"Bearer {self.sales_channel.access_token}"})
        session.headers.update({"Content-Type": "application/json"})

        self.api_host = host
        self.identity_host = identity_host
        self.api = session
        return session

    def get_marketplace_ids(self) -> list[str]:
        """Return list of marketplace IDs the account is subscribed to."""
        resp = self.api.get(f"{self.api_host}/sell/account/v1/subscription")
        if resp.ok:
            return [s.get("marketplaceId") for s in resp.json().get("subscriptions", [])]
        return []

    def get_default_marketplace_id(self) -> str | None:
        """Return the default marketplace ID for the account."""
        resp = self.api.get(f"{self.identity_host}/commerce/identity/v1/user")
        if resp.ok:
            return resp.json().get("registrationMarketplaceId")
        return None

    def get_marketplace_currency(self, marketplace_id: str) -> str | None:
        """Return the default currency code for a marketplace."""
        url = f"{self.api_host}/sell/metadata/v1/marketplace/{marketplace_id}/get_currencies"
        resp = self.api.get(url)
        if resp.ok:
            return resp.json().get("defaultCurrency", {}).get("code")
        return None

    @staticmethod
    def marketplace_reference() -> dict:
        """Return mapping from marketplace id to reference info."""
        return Reference.get_marketplace_id_values()
