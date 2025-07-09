import json

from django.conf import settings
from sp_api.base import SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient, DefinitionsApi, ListingsApi
from sales_channels.integrations.amazon.decorators import throttle_safe
from sales_channels.integrations.amazon.models import AmazonSalesChannelView
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.logs import RemoteLog


class PullAmazonMixin:

    def is_real_amazon_marketplace(self, marketplace) -> bool:
        domain = getattr(marketplace, "domain_name", "")
        name = getattr(marketplace, "name", "").lower()
        return domain.startswith("www.amazon.") and "non-amazon" not in name


class GetAmazonAPIMixin:
    """Mixin providing an authenticated Amazon SP-API client."""

    def update_assign_issues(
        self,
        issues,
        *,
        action_log=None,
        payload=None,
        log_identifier=None,
        submission_id=None,
        processing_status=None,
    ):
        """Update assign issues and optionally log the action."""
        if not getattr(self, "remote_product", None) or not isinstance(getattr(self, "view", None), AmazonSalesChannelView):
            return

        assign = SalesChannelViewAssign.objects.filter(
            product=self.remote_product.local_instance,
            sales_channel_view=self.view,
        ).first()
        if not assign:
            return

        if assign.remote_product_id != self.remote_product.id:
            assign.remote_product = self.remote_product

        assign.issues = [
            issue.to_dict() if hasattr(issue, "to_dict") else issue
            for issue in issues or []
        ]
        assign.save()

        if action_log and log_identifier:
            self.log_action(
                action_log,
                {},
                payload or {},
                log_identifier,
                submission_id=submission_id,
                processing_status=processing_status,
                issues=assign.issues,
            )

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
    def get_listing_item(self, sku, marketplace_id):
        """Return listing item payload for the given sku and marketplace."""
        listings = ListingsApi(self._get_client())
        resp = listings.get_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=sku,
            marketplace_ids=[marketplace_id],
        )
        return resp


    @throttle_safe(max_retries=5, base_delay=1)
    def get_listing_attributes(self, sku, marketplace_id):
        """Convenience wrapper returning attributes of a listing item."""
        payload = self.get_listing_item(sku, marketplace_id)

        if not payload:
            return {}

        if isinstance(payload, dict):
            return payload.get("attributes", {})

        return getattr(payload, "attributes", {}) or {}

    @throttle_safe(max_retries=5, base_delay=1)
    def _fetch_listing_items_page(self, listings_api, seller_id, marketplace_id, page_token=None, included_data=None):
        kwargs = {
            "seller_id": seller_id,
            "marketplace_ids": [marketplace_id],
            "page_size": 20,
            "included_data": included_data or ["summaries"],
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
        return [
            'AIR_PURIFIER', 'APPAREL', 'APPAREL_GLOVES',
            'APPAREL_HEAD_NECK_COVERING', 'APPAREL_PIN', 'BACKDROP',
            'BALLOON', 'BANNER', 'BASKET', 'BATHWATER_ADDITIVE',
            'BED_LINEN_SET', 'BLOWER_INFLATED_DECORATION', 'BODY_PAINT',
            'COAT', 'COORDINATED_OUTFIT', 'COSTUME_EYEWEAR',
            'COSTUME_HEADWEAR', 'COSTUME_MASK', 'COSTUME_OUTFIT',
            'CURTAIN', 'DARTBOARD', 'DECORATIVE_POM_POM',
            'DISHWARE_PLACE_SETTING', 'DISHWARE_PLATE', 'DRESS',
            'DRINKING_CUP', 'DRINKING_STRAW', 'FIGURINE', 'GARLAND',
            'GIFT_WRAP', 'GOLF_CLUB', 'HAIRBAND', 'HANDBAG', 'HAT',
            'HELMET', 'HOME', 'KICK_SCOOTER', 'KITCHEN_KNIFE',
            'MUSICAL_INSTRUMENT_TOY', 'NECKLACE', 'NECKTIE',
            'ONE_PIECE_OUTFIT', 'OUTERWEAR', 'PAJAMAS',
            'PARTY_DECORATION_PACK', 'PARTY_SUPPLIES', 'PET_APPAREL',
            'PINATA', 'PRETEND_PLAY_TOY', 'PRODUCT', 'PROTECTIVE_GLOVE',
            'ROBE', 'SALWAR_SUIT_SET', 'SCULPTURE', 'SHIRT', 'SKIRT',
            'SOCKS', 'SPORT_POM_POM', 'SQUEEZE_TOY', 'STORAGE_BOX',
            'SUIT', 'SUNGLASSES', 'SUSPENDER', 'TABLECLOTH', 'TIGHTS',
            'TOYS_AND_GAMES', 'TOY_BUILDING_BLOCK', 'TOY_FIGURE',
            'TOY_GUN', 'TRAY', 'VEST', 'WATER_FLOTATION_DEVICE', 'WIG',
            'WINDOW_FILM', 'WREATH'
        ]

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

    def get_all_products(self):
        listings_api = ListingsApi(self._get_client())
        seller_id = self.sales_channel.remote_id
        marketplace_ids = list(
            AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel)
            .values_list("remote_id", flat=True)
        )

        for marketplace_id in marketplace_ids:
            page_token = None
            while True:
                items, page_token = self._fetch_listing_items_page(
                    listings_api,
                    seller_id,
                    marketplace_id,
                    page_token,
                    included_data=["summaries", "attributes", "issues", "offers", "relationships"]
                )

                if hasattr(self, "total_import_instances_cnt"):
                    self.total_import_instances_cnt += len(items)
                    if hasattr(self, "set_threshold_chunk"):
                        self.set_threshold_chunk()

                for item in items:

                    import pprint
                    pprint.pprint(item.to_dict())

                    yield item

                if not page_token:
                    break

    def _get_issue_locale(self):
        from sales_channels.integrations.amazon.models import AmazonRemoteLanguage

        lang = self.sales_channel.multi_tenant_company.language
        remote_lang = AmazonRemoteLanguage.objects.filter(
            local_instance=lang, sales_channel_view__sales_channel=self.sales_channel
        ).first()
        return remote_lang.remote_code if remote_lang else None

    def _build_common_body(self, product_type, attributes):
        def clean(data):
            if isinstance(data, dict):
                return {k: clean(v) for k, v in data.items() if v is not None}
            if isinstance(data, list):
                return [clean(v) for v in data if v is not None]
            return data

        return {
            "productType": product_type,
            "requirements": "LISTING" if self.sales_channel.listing_owner else "LISTING_OFFER_ONLY",
            "attributes": clean(attributes),
        }

    @throttle_safe(max_retries=5, base_delay=1)
    def create_product(self, sku, marketplace_id, product_type, attributes):
        body = self._build_common_body(product_type, attributes)
        listings = ListingsApi(self._get_client())

        response = listings.put_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=sku,
            marketplace_ids=[marketplace_id],
            body=body,
            issue_locale=self._get_issue_locale(),
            mode="VALIDATION_PREVIEW" if settings.DEBUG else None,
        )

        print('--------------------------------------- ARGUMENTS')
        print('mode')
        print("VALIDATION_PREVIEW" if settings.DEBUG else None)
        print('body')
        import pprint
        pprint.pprint(body)
        print('-------------------------------------------------')

        submission_id = getattr(response, "submissionId", None)
        processing_status = getattr(response, "status", None) or getattr(response, "processingStatus", None)
        log_identifier, _ = self.get_identifiers()
        self.update_assign_issues(
            getattr(response, "issues", []) or [],
            action_log=RemoteLog.ACTION_CREATE,
            payload=body,
            log_identifier=log_identifier,
            submission_id=submission_id,
            processing_status=processing_status,
        )

        return response

    def _build_patches(self, current_attributes, new_attributes):
        """Generate JSON patches from current and new attributes."""

        def clean(data):
            if isinstance(data, dict):
                return {k: clean(v) for k, v in data.items() if v is not None}
            if isinstance(data, list):
                return [clean(v) for v in data if v is not None]
            return data

        patches = []
        current_attributes = current_attributes or {}
        new_attributes = new_attributes or {}

        for key, new_value in new_attributes.items():
            new_value = clean(new_value)
            current_value = current_attributes.get(key)

            if new_value is None:
                if key in current_attributes:
                    patches.append({"op": "delete", "value": [{key: current_value}]})
            else:
                if key not in current_attributes:
                    patches.append({"op": "add", "value": [{key: new_value}]})
                elif clean(current_value) != new_value:
                    patches.append({"op": "replace", "value": [{key: new_value}]})

        return patches

    @throttle_safe(max_retries=5, base_delay=1)
    def update_product(self, sku, marketplace_id, product_type, current_attributes, new_attributes):
        patches = self._build_patches(current_attributes, new_attributes)

        body = {
            "productType": product_type,
            "patches": patches,
        }

        listings = ListingsApi(self._get_client())
        response = listings.patch_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=sku,
            marketplace_ids=[marketplace_id],
            body=body,
            issue_locale=self._get_issue_locale(),
            mode="VALIDATION_PREVIEW" if settings.DEBUG else None,
        )

        submission_id = getattr(response, "submissionId", None)
        processing_status = getattr(response, "status", None) or getattr(response, "processingStatus", None)
        log_identifier, _ = self.get_identifiers()
        self.update_assign_issues(
            getattr(response, "issues", []) or [],
            action_log=RemoteLog.ACTION_UPDATE,
            payload=body,
            log_identifier=log_identifier,
            submission_id=submission_id,
            processing_status=processing_status,
        )

        return response
