"""Utility mixins for eBay API access."""

from __future__ import annotations

import requests
from django.conf import settings

import json

from ebay_rest import API
from ebay_rest.api import commerce_identity
from ebay_rest.reference import Reference
from ebay_rest.api.sell_marketing.api_client import ApiClient
from ebay_rest.api.sell_marketing.configuration import Configuration

from ebay_rest.api.commerce_identity.api.user_api import UserApi

from sales_channels.integrations.ebay.models import EbaySalesChannel


class GetEbayAPIMixin:

    def get_api(self) -> API:
        """Returns a fully authenticated API instance."""
        credentials = {
            "app_id": settings.EBAY_CLIENT_ID,
            "cert_id": settings.EBAY_CLIENT_SECRET,
            "dev_id": settings.EBAY_DEV_ID,
            "redirect_uri": settings.EBAY_RU_NAME,
        }

        user_info = {
            "refresh_token": self.sales_channel.refresh_token,
            "refresh_token_expiry": self.sales_channel.refresh_token_expiration.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "email_or_username": "OneSila",
            "password": "???"  # For some reason username and password are validating even if we provide the
            # refresh_token and we can add anything here
        }

        header = {
            # Use the marketplace of the store, e.g. "EBAY_FR", "EBAY_US", etc.
            "marketplace_id": "EBAY_GB",
            "accept_language": "en-GB",  # or "fr-FR", etc.
            "content_language": "en-GB",
        }

        # Construct API with dicts (no need for .json file)
        return API(
            application=credentials,
            user=user_info,
            header=header
        )

    def get_api_client(self) -> ApiClient:
        config = Configuration()
        access_token = self.api._user_token.get()

        config.access_token = access_token
        if getattr(self.sales_channel, "environment", None) == getattr(self.sales_channel.__class__, "SANDBOX", "sandbox"):
            config.host = "https://api.sandbox.ebay.com"
        else:
            config.host = "https://api.ebay.com"

        return ApiClient(configuration=config)

    def get_marketplace_currencies(self, marketplace_id: str) -> str | None:
        resp = self.api.sell_metadata_get_currencies(marketplace_id=marketplace_id)
        return resp

    def marketplace_reference(self) -> dict:
        """Return eBay marketplace reference information."""
        return Reference.get_marketplace_id_values()

    def get_marketplace_ids(self) -> list[str]:
        """Return all available marketplace IDs."""
        reference = self.marketplace_reference()
        return list(reference.keys())

    def get_default_marketplace_id(self) -> str | None:
        resp = self.api.commerce_identity_get_user()
        return resp.get("registration_marketplace_id", None)

    def _get_account_api_base_url(self) -> str:
        if  self.sales_channel.environment == EbaySalesChannel.SANDBOX:
            return "https://api.sandbox.ebay.com/sell/account/v1"

        return "https://api.ebay.com/sell/account/v1"

    def _get_account_headers(self) -> dict[str, str]:
        api = getattr(self, "api", None)
        if api is None:
            api = self.get_api()
            self.api = api
        access_token = api._user_token.get()
        if not access_token:
            raise ValueError("Unable to retrieve eBay access token.")
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    def _request_account_policy(self, endpoint: str, view_remote_id: str) -> dict:
        url = f"{self._get_account_api_base_url()}/{endpoint}"
        headers = self._get_account_headers()

        response = requests.get(url, headers=headers, params={"marketplace_id": view_remote_id})
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {}

    def get_fulfillment_policies(self) -> dict:
        return self._request_account_policy("fulfillment_policy", self.view.remote_id)

    def get_payment_policies(self) -> dict:
        return self._request_account_policy("payment_policy", self.view.remote_id)

    def get_return_policies(self) -> dict:
        return self._request_account_policy("return_policy", self.view.remote_id)

    def get_subscription_marketplace_ids(self) -> list[str] | None:
        url = f"{self._get_account_api_base_url()}/subscription"
        headers = self._get_account_headers()

        try:
            response = requests.get(url, headers=headers)
            if not response.ok:
                return None
            data = response.json()
        except Exception:
            return None

        marketplace_used_ids = set()

        for sub in data.get("subscriptions", []):
            marketplace_id = sub.get("marketplaceId")
            if marketplace_id:
                marketplace_used_ids.add(marketplace_id)

        return list(marketplace_used_ids)


