from core.logging_helpers import timeit_and_log
from properties.models import Property, PropertyTranslation
from sales_channels.integrations.amazon.constants import AMAZON_PATCH_SKIP_KEYS
from sales_channels.integrations.amazon.models.properties import AmazonProperty
import json

from django.conf import settings
from django.utils import timezone
from sp_api.base import SellingApiException
from spapi import SellersApi, SPAPIConfig, SPAPIClient, DefinitionsApi, ListingsApi
from sales_channels.integrations.amazon.decorators import throttle_safe
from sales_channels.integrations.amazon.models import AmazonSalesChannelView
from sales_channels.models.logs import RemoteLog
from deepdiff import DeepDiff

import pprint
import logging
logger = logging.getLogger(__name__)


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
        from sales_channels.integrations.amazon.factories.sales_channels.issues import FetchRemoteValidationIssueFactory

        """Update assign issues and optionally log the action."""
        if not getattr(self, "remote_product", None) or not isinstance(getattr(self, "view", None),
                                                                       AmazonSalesChannelView):
            return

        if getattr(self, "remote_instance", None) and isinstance(self.remote_instance, type(self.remote_product)):
            if self.remote_product.id != self.remote_instance.id:
                self.remote_product = self.remote_instance


        FetchRemoteValidationIssueFactory(
            remote_product=self.remote_product,
            view=self.view,
            issues=issues,
        ).run()

        if action_log and log_identifier:
            stored = self.remote_product.get_issues(self.view)
            self.log_action(
                action_log,
                {},
                payload or {},
                log_identifier,
                submission_id=submission_id,
                processing_status=processing_status,
                issues=stored,
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

    @timeit_and_log(logger)
    @throttle_safe(max_retries=5, base_delay=1)
    def _fetch_listing_items_page(
            self,
            listings_api,
            seller_id,
            marketplace_id,
            page_token=None,
            included_data=None,
            issue_locale=None,
            sort_by=None,
            sort_order=None,
            created_after=None,
            created_before=None,
    ):
        kwargs = {
            "seller_id": seller_id,
            "marketplace_ids": [marketplace_id],
            "page_size": 20,
            "included_data": included_data or ["summaries"],
            "issue_locale": issue_locale,
        }

        if page_token:
            kwargs["page_token"] = page_token

        if sort_by:
            kwargs["sort_by"] = sort_by
        if sort_order:
            kwargs["sort_order"] = sort_order
        if created_after:
            kwargs["created_after"] = created_after
        if created_before:
            kwargs["created_before"] = created_before

        response = listings_api.search_listings_items(**kwargs)

        items = response.items or []
        next_token = (
            response.pagination.next_token
            if response.pagination and hasattr(response.pagination, "next_token")
            else None
        )
        results_number = getattr(response, "number_of_results", None)

        return items, next_token, results_number

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

    def get_all_products_by_marketplace(self, marketplace_id: str, listings_api, seller_id, issue_locale, given_created_after=None):

        created_after = given_created_after
        while True:
            page_token = None
            last_created_date = None

            logger.info(f"[START CYCLE] created_after={created_after}")

            while True:
                items, page_token, results_number = self._fetch_listing_items_page(
                    listings_api,
                    seller_id,
                    marketplace_id,
                    page_token=page_token,
                    included_data=["summaries", "attributes", "issues", "offers", "relationships"],
                    issue_locale=issue_locale,
                    sort_by="createdDate",
                    sort_order="ASC",
                    created_after=created_after
                )

                total_results = results_number or 0

                for item in items:
                    summaries = getattr(item, "summaries", None)
                    if summaries:
                        summary = summaries[0]
                        created = getattr(summary, "created_date", None)
                        if created:
                            last_created_date = created

                    yield item

                if not page_token:
                    break

            logger.info(
                f"[END CYCLE] results_number={total_results} | last_created_date={last_created_date}"
            )

            # amazon items results is limited at 1000
            if total_results < 1000:
                break

            if not last_created_date:
                break

            created_after = last_created_date

    def get_all_products(self):
        listings_api = ListingsApi(self._get_client())
        seller_id = self.sales_channel.remote_id
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=self.sales_channel
        ).order_by("-is_default")
        marketplace_ids = list(views.values_list("remote_id", flat=True))
        issue_locale = self._get_issue_locale()

        for marketplace_id in marketplace_ids:
            yield from self.get_all_products_by_marketplace(
                marketplace_id,
                listings_api,
                seller_id,
                issue_locale
            )

    def get_total_number_of_products(self) -> int:
        listings_api = ListingsApi(self._get_client())
        seller_id = self.sales_channel.remote_id
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=self.sales_channel
        ).order_by("-is_default")
        marketplace_ids = list(views.values_list("remote_id", flat=True))
        issue_locale = self._get_issue_locale()

        total = 0
        for marketplace_id in marketplace_ids:
            items, _, results_number = self._fetch_listing_items_page(
                listings_api,
                seller_id,
                marketplace_id,
                page_token=None,
                included_data=["summaries"],
                issue_locale=issue_locale,
                sort_by="createdDate",
                sort_order="ASC"
            )
            total += results_number or 0

        return total

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
        remote_product = getattr(self, "remote_product", getattr(self, "remote_instance", None))
        created = getattr(remote_product, "created_marketplaces", []) or []

        first_assign = not created
        requirements = "LISTING" if (first_assign and not has_asin) or remote_product.product_owner else "LISTING_OFFER_ONLY"

        if requirements == "LISTING_OFFER_ONLY":
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
            "requirements": requirements,
            "attributes": clean(attributes),
        }

    def _build_listing_kwargs(self, sku, marketplace_id, body, force_validation_only=False):
        kwargs = {
            "seller_id": self.sales_channel.remote_id,
            "sku": sku,
            "marketplace_ids": [marketplace_id],
            "body": body,
            "issue_locale": self._get_issue_locale(),
        }

        if settings.DEBUG or force_validation_only:
            kwargs["mode"] = "VALIDATION_PREVIEW"

        return kwargs

    @throttle_safe(max_retries=5, base_delay=1)
    def create_product(
        self, sku, marketplace_id, product_type, attributes, force_validation_only: bool = False
    ):
        body = self._build_common_body(product_type, attributes)
        listings = ListingsApi(self._get_client())

        logger.info(
            "create_product arguments: mode=%s body=%s",
            "VALIDATION_PREVIEW" if settings.DEBUG or force_validation_only else None,
            pprint.pformat(body),
        )

        response = listings.put_listings_item(
            **self._build_listing_kwargs(sku, marketplace_id, body, force_validation_only))

        if getattr(self, "remote_product", None):
            self.remote_product.last_sync_at = timezone.now()
            self.remote_product.save(update_fields=["last_sync_at"])

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

        logger.info("create_product response:\n%s", pprint.pformat(response))

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

        skip_keys = AMAZON_PATCH_SKIP_KEYS

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
                    patches.append({"op": "replace", "path": path, "value": new_value})
                else:
                    diff = DeepDiff(current_value, new_value, ignore_order=True)
                    if diff:
                        patches.append({"op": "replace", "path": path, "value": new_value})

        return patches

    @throttle_safe(max_retries=1, base_delay=1)
    def update_product(
        self,
        sku,
        marketplace_id,
        product_type,
        new_attributes,
        current_attributes=None,
        force_validation_only: bool = False,
    ):
        if current_attributes is None or current_attributes == {}:
            current_attributes = self.get_listing_attributes(sku, marketplace_id)

        patches = self._build_patches(current_attributes, new_attributes)
        body = {
            "productType": product_type.product_type_code,
            "patches": patches,
        }
        logger.info(
            "update_product current attributes:\n%s",
            pprint.pformat(current_attributes),
        )
        logger.info(
            "update_product new attributes:\n%s",
            pprint.pformat(new_attributes),
        )
        logger.info(
            "update_product arguments: mode=%s body=%s",
            "VALIDATION_PREVIEW" if settings.DEBUG or force_validation_only else None,
            pprint.pformat(body),
        )

        listings = ListingsApi(self._get_client())
        response = listings.patch_listings_item(**self._build_listing_kwargs(sku, marketplace_id, body, force_validation_only))


        if getattr(self, "remote_product", None):
            self.remote_product.last_sync_at = timezone.now()
            self.remote_product.save(update_fields=["last_sync_at"])
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

        logger.info("update_product response:\n%s", pprint.pformat(response))

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
