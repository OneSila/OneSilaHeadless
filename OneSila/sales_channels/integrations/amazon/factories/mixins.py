from django.conf import settings
from sp_api.base import  SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient

class GetAmazonAPIMixin:
    """Mixin providing an authenticated Amazon SP-API client."""

    def get_marketplaces(self):
        """Fetches all marketplaces the seller is participating in."""

        config = SPAPIConfig(
            client_id=settings.AMAZON_CLIENT_ID,
            client_secret=settings.AMAZON_CLIENT_SECRET,
            refresh_token=self.sales_channel.refresh_token,
            region=self.sales_channel.region,
        )

        client = SPAPIClient(config)
        sellers_api = SellersApi(client.api_client)

        try:
            response = sellers_api.get_marketplace_participations()
            return response.payload
        except SellingApiException as e:
            raise Exception(f"SP-API failed: {e}")