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
            "marketplace_id": "EBAY_US",
            "accept_language": "en-US",  # or "fr-FR", etc.
            "content_language": "en-US",
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
        # ``ebay_rest`` does not expose an endpoint that returns the list of
        # marketplaces an account has access to.  For the pull factories we only
        # need the list of known marketplace identifiers, which can be obtained
        # from the ``Reference`` helper shipped with the library.

        reference = self.marketplace_reference()
        return list(reference.keys())
        # client = self.get_api_client()
        #
        # response = client.call_api(
        #     resource_path="/sell/account/v1/subscription",
        #     method="GET",
        #     auth_settings=["api_auth"],
        #     header_params={"Content-Type": "application/json"},
        #     response_type="dict",
        # )
        #
        # return [s["marketplaceId"] for s in response[0].get("subscriptions", [])]

    def get_default_marketplace_id(self) -> str | None:
        resp = self.api.commerce_identity_get_user()
        return resp.get("registration_marketplace_id", None)
