from django.conf import settings
from sp_api.base import  SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient, DefinitionsApi, ListingsApi

import logging

from sales_channels.integrations.amazon.decorators import throttle_safe

# Mute sp-api logs
logging.getLogger("sp_api").setLevel(logging.WARNING)
logging.getLogger("spapi").setLevel(logging.WARNING)

# Optional: If they're flooding stdout handlers
logging.getLogger("sp_api").propagate = False
logging.getLogger("spapi").propagate = False

from sales_channels.integrations.amazon.models import AmazonSalesChannelView

class PullAmazonMixin:

    def is_real_amazon_marketplace(self, marketplace) -> bool:
        domain = getattr(marketplace, "domain_name", "")
        name = getattr(marketplace, "name", "").lower()
        return domain.startswith("www.amazon.") and "non-amazon" not in name

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


    @throttle_safe(max_retries=5, base_delay=1)
    def _fetch_listing_items_page(self, listings_api, seller_id, marketplace_id, page_token=None):
        kwargs = {
            "seller_id": seller_id,
            "marketplace_ids": [marketplace_id],
            "page_size": 20,
            "included_data": ["summaries"],
        }
        if page_token:
            kwargs["page_token"] = page_token

        response = listings_api.search_listings_items(**kwargs)
        items = response.items or []
        next_token = (
            response.pagination.next_token
            if response.pagination and hasattr(response.pagination, "next_token")
            else None
        )
        return items, next_token

    def get_product_types(self):
        # @TODO: DON'T FORGET TO REMOVE THAT
        return ['AIR_PURIFIER', 'APPAREL', 'APPAREL_GLOVES', 'APPAREL_HEAD_NECK_COVERING', 'APPAREL_PIN', 'BACKDROP', 'BALLOON', 'BANNER', 'BASKET', 'BATHWATER_ADDITIVE', 'BED_LINEN_SET', 'BLOWER_INFLATED_DECORATION', 'BODY_PAINT', 'COAT', 'COORDINATED_OUTFIT', 'COSTUME_EYEWEAR', 'COSTUME_HEADWEAR', 'COSTUME_MASK', 'COSTUME_OUTFIT', 'CURTAIN', 'DARTBOARD', 'DECORATIVE_POM_POM', 'DISHWARE_PLACE_SETTING', 'DISHWARE_PLATE', 'DRESS', 'DRINKING_CUP', 'DRINKING_STRAW', 'FIGURINE', 'GARLAND', 'GIFT_WRAP', 'GOLF_CLUB', 'HAIRBAND', 'HANDBAG', 'HAT', 'HELMET', 'HOME', 'KICK_SCOOTER', 'KITCHEN_KNIFE', 'MUSICAL_INSTRUMENT_TOY', 'NECKLACE', 'NECKTIE', 'ONE_PIECE_OUTFIT', 'OUTERWEAR', 'PAJAMAS', 'PARTY_DECORATION_PACK', 'PARTY_SUPPLIES', 'PET_APPAREL', 'PINATA', 'PRETEND_PLAY_TOY', 'PRODUCT', 'PROTECTIVE_GLOVE', 'ROBE', 'SALWAR_SUIT_SET', 'SCULPTURE', 'SHIRT', 'SKIRT', 'SOCKS', 'SPORT_POM_POM', 'SQUEEZE_TOY', 'STORAGE_BOX', 'SUIT', 'SUNGLASSES', 'SUSPENDER', 'TABLECLOTH', 'TIGHTS', 'TOYS_AND_GAMES', 'TOY_BUILDING_BLOCK', 'TOY_FIGURE', 'TOY_GUN', 'TRAY', 'VEST', 'WATER_FLOTATION_DEVICE', 'WIG', 'WINDOW_FILM', 'WREATH']

        listings_api = ListingsApi(self._get_client())
        seller_id = self.sales_channel.remote_id
        marketplace_ids = list(
            AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel)
            .values_list("remote_id", flat=True)
        )

        product_types = set()

        for marketplace_id in marketplace_ids:
            page_token = None
            while True:
                items, page_token = self._fetch_listing_items_page(
                    listings_api, seller_id, marketplace_id, page_token
                )

                for item in items:
                    summaries = item.summaries or []
                    for summary in summaries:
                        pt = summary.product_type
                        if pt:
                            product_types.add(pt)

                if not page_token:
                    break

        return sorted(product_types)