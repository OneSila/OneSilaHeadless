import hashlib
import os

import requests
from django.conf import settings
from sp_api.base import  SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient, DefinitionsApi, ListingsApi

import logging

from properties.models import ProductPropertiesRuleItem
from sales_channels.integrations.amazon.constants import AMAZON_LOCALE_MAPPING, AMAZON_INTERNAL_PROPERTIES
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

    def _download_json(self, url, category_code=None, marketplace_id=None):
        """
        Download the JSON schema from Amazon's URL and save it to disk for inspection.
        """
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        SCHEMA_DUMP_DIR = "./amazon_schema_dumps"

        # Ensure the dump directory exists
        os.makedirs(SCHEMA_DUMP_DIR, exist_ok=True)

        # Create a safe filename
        hash_part = hashlib.md5(url.encode()).hexdigest()[:8]
        filename_parts = [category_code or "unknown", marketplace_id or "unknown", hash_part]
        filename = "_".join(filter(None, filename_parts)) + ".json"

        filepath = os.path.join(SCHEMA_DUMP_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Schema saved to: {filepath}")
        return data

    @throttle_safe(max_retries=5, base_delay=1)
    def _get_schema_for_marketplace(self, view, category_code, is_default_marketplace=False):
        """
        SP-API call to get product type definition for a given marketplace view.
        Returns parsed schema JSON with optional title added.
        """
        definitions_api = DefinitionsApi(self._get_client())
        response = definitions_api.get_definitions_product_type(
            product_type=category_code,
            marketplace_ids=[view.remote_id],
            requirements="LISTING",
            seller_id=self.sales_channel.remote_id,
        )

        schema_link = response.var_schema.link.resource
        schema_data = self._download_json(schema_link)

        if is_default_marketplace:
            schema_data["title"] = response.display_name  # manually inject category title
            print('------------------------------------------------------------- IS DEFAULT WE ADD TITLE')

        return schema_data

    def get_product_type_definition(self, category_code):
        """
        Fetch full definition of a product type from Amazon SP-API and return
        a normalized structure with required/optional fields and enum values.
        """
        sales_channel_views = AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel)
        marketplace_schemas = {}
        default_schema = None

        # Step 1: Get schemas for all marketplaces
        for view in sales_channel_views:
            lang = view.remote_languages.first()
            is_default = lang and self.sales_channel.country and self.sales_channel.country in lang.remote_code

            schema_data = self._get_schema_for_marketplace(view, category_code, is_default_marketplace=is_default)
            marketplace_schemas[view.remote_id] = schema_data
            if is_default:
                default_schema = schema_data

        if not default_schema:
            raise Exception("No valid default schema found (based on country match).")

        default_required_keys = default_schema.get("required", [])
        default_properties = default_schema.get("properties", {})
        category_name = default_schema.get("title", category_code)

        final_items = {}

        # Step 2: Loop through all schemas and gather all properties (with enums)
        for marketplace_id, schema in marketplace_schemas.items():
            properties = schema.get("properties", {})
            required_keys = schema.get("required", [])

            for attr_code, prop in properties.items():
                if attr_code in AMAZON_INTERNAL_PROPERTIES:
                    continue

                is_required = attr_code in default_required_keys or attr_code in required_keys
                prop_type = ProductPropertiesRuleItem.REQUIRED if is_required else ProductPropertiesRuleItem.OPTIONAL

                # Title from default schema if exists, otherwise fallback to current
                if attr_code in default_properties:
                    title = default_properties[attr_code].get("title", attr_code)
                else:
                    title = prop.get("title", attr_code)

                if attr_code not in final_items:
                    final_items[attr_code] = {
                        "type": prop_type,
                        "property": {
                            "attribute_code": attr_code,
                            "name": title,
                            "values": []
                        }
                    }

                # Add values
                print(f'---------------------------------------------------------- PROP {attr_code}')

                import pprint
                pprint.pprint(prop)
                enums = prop.get("enum")
                enum_names = prop.get("enumNames")
                if enums and enum_names:
                    for val, label in zip(enums, enum_names):
                        value_obj = {
                            "value": val,
                            "name": label,
                            "marketplace_id": marketplace_id
                        }
                        if value_obj not in final_items[attr_code]["property"]["values"]:
                            final_items[attr_code]["property"]["values"].append(value_obj)

        return {
            "name": category_name,
            "category_code": category_code,
            "items": list(final_items.values())
        }

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