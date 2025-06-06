from django.conf import settings
from sp_api.base import  SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient, DefinitionsApi, ListingsApi

from sales_channels.integrations.amazon.models import AmazonSalesChannelView


class GetAmazonAPIMixin:
    """Mixin providing an authenticated Amazon SP-API client."""

    def _get_client(self):
        config = SPAPIConfig(
            client_id=settings.AMAZON_CLIENT_ID,
            client_secret=settings.AMAZON_CLIENT_SECRET,
            refresh_token=self.sales_channel.refresh_token,
            region=self.sales_channel.region,
        )
        return SPAPIClient(config).api_client

    def get_api(self):
        return None

    def get_marketplaces(self):
        """Fetches all marketplaces the seller is participating in."""

        sellers_api = SellersApi(self._get_client())

        try:
            response = sellers_api.get_marketplace_participations()
            return response.payload
        except SellingApiException as e:
            raise Exception(f"SP-API failed: {e}")


    # def get_product_types(self):
    #
    #     definitions_api = DefinitionsApi(self._get_client())
    #     marketplace_ids = list(AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel).values_list('remote_id', flat=True))
    #     print(marketplace_ids)
    #
    #     try:
    #
    #         response = definitions_api.search_definitions_product_types(
    #             marketplace_ids=marketplace_ids,
    #         )
    #         print('---------------------------__ RESPONSE')
    #         return response.payload
    #     except Exception as e:
    #         raise Exception(f"Failed to fetch product types: {e}")
    #
    # def get_product_types(self):
    #     listings_api = ListingsApi(self._get_client())
    #
    #     seller_id = self.sales_channel.remote_id
    #     marketplace_ids = list(
    #         AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel)
    #         .values_list("remote_id", flat=True)
    #     )
    #
    #     product_types = set()
    #
    #     for marketplace_id in marketplace_ids:
    #         page_token = None
    #         while True:
    #             kwargs = {
    #                 "seller_id": seller_id,
    #                 "marketplace_ids": [marketplace_id],
    #                 "page_size": 20,
    #                 "included_data": ["summaries"],
    #                 # "with_status": ["BUYABLE"],
    #             }
    #
    #             print(kwargs)
    #             if page_token:
    #                 kwargs["page_token"] = page_token
    #
    #             response = listings_api.search_listings_items(**kwargs)
    #             items = response.items or []
    #
    #             for item in items:
    #                 summaries = item.summaries or []
    #                 for summary in summaries:
    #                     pt = summary.product_type
    #                     if pt:
    #                         product_types.add(pt)
    #
    #             page_token = (
    #                 response.pagination.next_token
    #                 if response.pagination and hasattr(response.pagination, "next_token")
    #                 else None
    #             )
    #             if not page_token:
    #                 break
    #
    #     return sorted(product_types)