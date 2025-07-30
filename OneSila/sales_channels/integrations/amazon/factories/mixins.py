import json

from django.conf import settings
from sp_api.base import SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient, DefinitionsApi, ListingsApi
from sales_channels.integrations.amazon.decorators import throttle_safe
from sales_channels.integrations.amazon.models import AmazonSalesChannelView
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.logs import RemoteLog
from core.helpers import ensure_serializable
from deepdiff import DeepDiff


from sales_channels.integrations.amazon.models.properties import AmazonProperty
from properties.models import Property, PropertyTranslation


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
        if not getattr(self, "remote_product", None) or not isinstance(getattr(self, "view", None),
                                                                       AmazonSalesChannelView):
            return

        assign = SalesChannelViewAssign.objects.filter(
            product=self.remote_product.local_instance,
            sales_channel_view=self.view,
        ).first()
        if not assign:
            return

        if assign.remote_product_id != self.remote_product.id:
            assign.remote_product = self.remote_product

        existing_issues = assign.issues or []

        # Ensure each existing issue is a dictionary
        existing_issues_dicts = [
            ensure_serializable(issue.to_dict() if hasattr(issue, "to_dict") else issue)
            for issue in existing_issues
        ]

        new_issues = []
        for issue in issues or []:
            issue_dict = ensure_serializable(
                issue.to_dict() if hasattr(issue, "to_dict") else issue
            )
            issue_dict["validation_issue"] = True

            if issue_dict not in existing_issues_dicts:
                new_issues.append(issue_dict)

        if new_issues:
            assign.issues = existing_issues_dicts + new_issues
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
    def search_product_types(self, marketplace_id: str, name: str | None = None) -> dict:
        """Return product type suggestions for an item name."""
        definitions_api = DefinitionsApi(self._get_client())

        kwargs = {
            'marketplace_ids': [marketplace_id],
            'locale': self._get_issue_locale()
        }

        if name is not None:
            kwargs['item_name'] = name

        resp = definitions_api.search_definitions_product_types(**kwargs)

        if hasattr(resp, "to_dict"):
            return resp.to_dict()

        return resp

    @throttle_safe(max_retries=5, base_delay=1)
    def get_listing_item(self, sku, marketplace_id, *, included_data=None, issue_locale=None):
        """Return listing item payload for the given sku and marketplace."""

        if issue_locale is None:
            issue_locale = self._get_issue_locale()

        listings = ListingsApi(self._get_client())
        resp = listings.get_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=sku,
            marketplace_ids=[marketplace_id],
            included_data=included_data or ["summaries", "issues"],
            issue_locale=issue_locale,
        )
        return resp

    @throttle_safe(max_retries=5, base_delay=1)
    def get_listing_attributes(self, sku, marketplace_id):
        """Convenience wrapper returning attributes of a listing item."""
        payload = self.get_listing_item(sku, marketplace_id, included_data=["attributes"],)

        if not payload:
            return {}

        if isinstance(payload, dict):
            return payload.get("attributes", {})

        return getattr(payload, "attributes", {}) or {}

    @throttle_safe(max_retries=5, base_delay=1)
    def _fetch_listing_items_page(self, listings_api, seller_id, marketplace_id, page_token=None, included_data=None, issue_locale=None):
        kwargs = {
            "seller_id": seller_id,
            "marketplace_ids": [marketplace_id],
            "page_size": 20,
            "included_data": included_data or ["summaries"],
            "issue_locale": issue_locale
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
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=self.sales_channel
        ).order_by("-is_default")
        marketplace_ids = list(views.values_list("remote_id", flat=True))

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
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=self.sales_channel
        ).order_by("-is_default")
        marketplace_ids = list(views.values_list("remote_id", flat=True))
        issue_locale = self._get_issue_locale()
        import pprint

        for marketplace_id in marketplace_ids:
            page_token = None
            while True:
                items, page_token = self._fetch_listing_items_page(
                    listings_api,
                    seller_id,
                    marketplace_id,
                    page_token,
                    included_data=["summaries", "attributes", "issues", "offers", "relationships"],
                    issue_locale=issue_locale
                )

                if hasattr(self, "total_import_instances_cnt"):
                    self.total_import_instances_cnt += len(items)
                    if hasattr(self, "set_threshold_chunk"):
                        self.set_threshold_chunk()

                for item in items:
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
        """Return body for Amazon create/update requests."""

        def clean(data):
            if isinstance(data, dict):
                return {k: clean(v) for k, v in data.items() if v is not None}
            if isinstance(data, list):
                return [clean(v) for v in data if v is not None]
            return data

        pt_code = product_type.product_type_code
        has_asin = "merchant_suggested_asin" in (attributes or {})
        force_listing = getattr(self, "force_listing_requirements", False)
        remote_product = getattr(self, "remote_product", getattr(self, "remote_instance", None))
        product_owner = getattr(remote_product, "product_owner", False)

        is_new_listing = has_asin or force_listing

        if not (self.sales_channel.listing_owner or product_owner) and not is_new_listing:
            region = self.view.api_region_code
            allowed_keys = (
                product_type.listing_offer_required_properties.get(region, [])
                if isinstance(product_type.listing_offer_required_properties, dict)
                else []
            )
            if allowed_keys:
                attributes = {k: v for k, v in (attributes or {}).items() if k in allowed_keys}

        return {
            "productType": pt_code,
            "requirements": "LISTING" if (self.sales_channel.listing_owner or product_owner or is_new_listing) else "LISTING_OFFER_ONLY",
            "attributes": clean(attributes),
        }

    @throttle_safe(max_retries=5, base_delay=1)
    def create_product(self, sku, marketplace_id, product_type, attributes):
        body = self._build_common_body(product_type, attributes)
        listings = ListingsApi(self._get_client())

        # print('--------------------------------------- ARGUMENTS')
        # print('mode')
        # print("VALIDATION_PREVIEW" if settings.DEBUG else None)
        # print('body')
        # import pprint
        # pprint.pprint(body)
        # print('-------------------------------------------------')

        response = listings.put_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=sku,
            marketplace_ids=[marketplace_id],
            body=body,
            issue_locale=self._get_issue_locale(),
            mode="VALIDATION_PREVIEW" if settings.DEBUG else None,
        )

        submission_id = getattr(response, "submission_id", None)
        processing_status = getattr(response, "status", None)
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

        skip_keys = {
            "merchant_suggested_asin",
            "externally_assigned_product_identifier",
            "supplier_declared_has_product_identifier_exemption"
        }

        for key, new_value in new_attributes.items():
            if key in skip_keys:
                continue
            new_value = clean(new_value)
            current_value = current_attributes.get(key)
            path = f"/attributes/{key}"

            if new_value is None:
                if key in current_attributes:
                    patches.append({"op": "delete", "path": path})
            else:
                if key not in current_attributes:
                    patches.append({"op": "add", "path": path, "value": new_value})
                else:
                    diff = DeepDiff(current_value, new_value, ignore_order=True)
                    if diff:
                        patches.append({"op": "replace", "path": path, "value": new_value})

        return patches

    @throttle_safe(max_retries=5, base_delay=1)
    def update_product(
        self,
        sku,
        marketplace_id,
        product_type,
        new_attributes,
        current_attributes=None,
    ):
        if current_attributes is None or current_attributes == {}:
            current_attributes = self.get_listing_attributes(sku, marketplace_id)

        patches = self._build_patches(current_attributes, new_attributes)
        body = {
            "productType": product_type.product_type_code,
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
        submission_id = getattr(response, "submission_id", None)
        processing_status = getattr(response, "status", None)
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


class EnsureMerchantSuggestedAsinMixin:
    """Mixin ensuring the merchant_suggested_asin property exists."""

    def _ensure_merchant_suggested_asin(self):
        remote_property, _ = AmazonProperty.objects.get_or_create(
            allow_multiple=True,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="merchant_suggested_asin",
            defaults={"type": Property.TYPES.TEXT},
        )

        if not remote_property.local_instance:
            local_property, _ = Property.objects.get_or_create(
                internal_name="merchant_suggested_asin",
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={
                    "type": Property.TYPES.TEXT,
                    "non_deletable": True,
                },
            )

            PropertyTranslation.objects.get_or_create(
                property=local_property,
                language=self.sales_channel.multi_tenant_company.language,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={"name": "Amazon Asin"},
            )

            remote_property.local_instance = local_property
            remote_property.save()

        local_property = remote_property.local_instance
        if not local_property.non_deletable:
            local_property.non_deletable = True
            local_property.save(update_fields=["non_deletable"])

        return remote_property


class EnsureGtinExemptionMixin:
    """Mixin ensuring the supplier_declared_has_product_identifier_exemption property exists."""

    def _ensure_gtin_exemption(self):
        remote_property, _ = AmazonProperty.objects.get_or_create(
            allow_multiple=True,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="supplier_declared_has_product_identifier_exemption",
            defaults={"type": Property.TYPES.BOOLEAN},
        )

        if not remote_property.local_instance:
            local_property, _ = Property.objects.get_or_create(
                internal_name="supplier_declared_has_product_identifier_exemption",
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={"type": Property.TYPES.BOOLEAN},
            )

            PropertyTranslation.objects.get_or_create(
                property=local_property,
                language=self.sales_channel.multi_tenant_company.language,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={"name": "GTIN Exemption"},
            )

            remote_property.local_instance = local_property
            remote_property.save()

        return remote_property
