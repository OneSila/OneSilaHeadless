"""Utility mixins for eBay API access."""

from __future__ import annotations

import json
from ebay_rest.reference import Reference
from ebay_rest.api.sell_marketing.api_client import ApiClient
from ebay_rest.api.sell_marketing.configuration import Configuration

from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannel


class GetEbayAPIMixin:
    """Mixin providing a simple authenticated API client for eBay."""

    api: ApiClient
    api_host: str
    identity_host: str

    def get_api(self) -> ApiClient:
        """Return an authenticated :class:`ApiClient` for eBay APIs."""

        host = "https://api.ebay.com"
        identity_host = "https://apiz.ebay.com"
        if getattr(self.sales_channel, "environment", EbaySalesChannel.PRODUCTION) == EbaySalesChannel.SANDBOX:
            host = "https://api.sandbox.ebay.com"
            identity_host = "https://apiz.sandbox.ebay.com"

        configuration = Configuration()
        configuration.host = host
        token = getattr(self.sales_channel, "access_token", None)
        if token:
            configuration.access_token = token
        api_client = ApiClient(configuration)
        api_client.default_headers.update({"Content-Type": "application/json"})

        self.api_host = host
        self.identity_host = identity_host
        self.api = api_client
        return api_client

    def get_marketplace_ids(self) -> list[str]:
        """Return list of marketplace IDs the account is subscribed to."""
        resp = self.api.request(
            "GET",
            f"{self.api_host}/sell/account/v1/subscription",
            headers=self.api.default_headers,
        )
        if resp.status < 300:
            data = json.loads(resp.data)
            return [s.get("marketplaceId") for s in data.get("subscriptions", [])]
        return []

    def get_default_marketplace_id(self) -> str | None:
        """Return the default marketplace ID for the account."""
        resp = self.api.request(
            "GET",
            f"{self.identity_host}/commerce/identity/v1/user",
            headers=self.api.default_headers,
        )
        if resp.status < 300:
            data = json.loads(resp.data)
            return data.get("registrationMarketplaceId")
        return None

    def get_marketplace_currency(self, marketplace_id: str) -> str | None:
        """Return the default currency code for a marketplace."""
        url = f"{self.api_host}/sell/metadata/v1/marketplace/{marketplace_id}/get_currencies"
        resp = self.api.request("GET", url, headers=self.api.default_headers)
        if resp.status < 300:
            data = json.loads(resp.data)
            return data.get("defaultCurrency", {}).get("code")
        return None

    @staticmethod
    def marketplace_reference() -> dict:
        """Return mapping from marketplace id to reference info."""
        return Reference.get_marketplace_id_values()
