import json
from typing import Dict

from products.models import Product, ProductTranslation, ProductTranslationBulletPoint
from properties.models import Property, ProductProperty
from sales_channels.factories.products.products import (
    RemoteProductSyncFactory,
    RemoteProductCreateFactory,
    RemoteProductUpdateFactory,
    RemoteProductDeleteFactory,
)
from sales_channels.integrations.amazon.factories.mixins import (
    GetAmazonAPIMixin,
    AmazonListingIssuesMixin,
)
from sales_channels.integrations.amazon.factories.products.images import (
    AmazonMediaProductThroughCreateFactory,
    AmazonMediaProductThroughUpdateFactory,
    AmazonMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.amazon.factories.properties import (
    AmazonProductPropertyCreateFactory,
    AmazonProductPropertyUpdateFactory,
    AmazonProductPropertyDeleteFactory,
)
from sales_channels.integrations.amazon.factories.products.content import (
    AmazonProductContentUpdateFactory,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonProduct,
)
from sales_channels.integrations.amazon.models.properties import AmazonProductProperty, AmazonProperty
from sales_channels.integrations.amazon.models import AmazonCurrency
from sales_channels.exceptions import SwitchedToCreateException, SwitchedToSyncException
from spapi import ListingsApi

import logging

logger = logging.getLogger(__name__)


class AmazonProductBaseFactory(GetAmazonAPIMixin, AmazonListingIssuesMixin, RemoteProductSyncFactory):
    remote_model_class = AmazonProduct
    remote_image_assign_create_factory = AmazonMediaProductThroughCreateFactory
    remote_image_assign_update_factory = AmazonMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = AmazonMediaProductThroughDeleteFactory

    remote_product_property_class = AmazonProductProperty
    remote_product_property_create_factory = AmazonProductPropertyCreateFactory
    remote_product_property_update_factory = AmazonProductPropertyUpdateFactory
    remote_product_property_delete_factory = AmazonProductPropertyDeleteFactory

    REMOTE_TYPE_SIMPLE = "PRODUCT"
    REMOTE_TYPE_CONFIGURABLE = "PRODUCT"

    field_mapping = {}

    def get_sync_product_factory(self):
        from sales_channels.integrations.amazon.factories.products import AmazonProductSyncFactory
        return AmazonProductSyncFactory

    def get_create_product_factory(self):
        from sales_channels.integrations.amazon.factories.products import AmazonProductCreateFactory
        return AmazonProductCreateFactory

    def get_delete_product_factory(self):
        from sales_channels.integrations.amazon.factories.products import AmazonProductDeleteFactory
        return AmazonProductDeleteFactory

    # Expose as properties
    sync_product_factory = property(get_sync_product_factory)
    create_product_factory = property(get_create_product_factory)
    delete_product_factory = property(get_delete_product_factory)

    def __init__(self, *args, view=None, **kwargs):
        if view is None:
            raise ValueError("AmazonProduct factories require a view argument")
        self.view = view
        super().__init__(*args, **kwargs)
        self.attributes: Dict = {}
        self.image_attributes: Dict = {}

    # ------------------------------------------------------------
    # Preflight & initialization helpers
    # ------------------------------------------------------------
    def preflight_check(self):
        if not super().preflight_check():
            return False
        if self.is_create:
            if not self._get_asin() and not self.get_ean_code_value():
                raise ValueError("Amazon listings require ASIN or EAN on create")
        return True

    def initialize_remote_product(self):
        super().initialize_remote_product()
        if self.is_create and self.view.remote_id in (self.remote_instance.created_marketplaces or []):
            raise SwitchedToSyncException("Listing already created for marketplace")
        if not self.is_create and self.view.remote_id not in (self.remote_instance.created_marketplaces or []):
            raise SwitchedToCreateException("Listing missing for marketplace")

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _get_asin(self) -> str | None:
        amazon_prop = AmazonProperty.objects.get(
            code="merchant_suggested_asin",
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
        )

        if amazon_prop.local_instance is None:
            return None


        pp = ProductProperty.objects.filter(product=self.local_instance, property=amazon_prop.local_instance).first()
        return pp.get_value() if pp else None

    def _get_ean_for_payload(self) -> str | None:
        return self.remote_instance.ean_code or self.get_ean_code_value()

    def build_basic_attributes(self) -> Dict:
        attrs: Dict = {}
        asin = self._get_asin()
        if asin:
            attrs["merchant_suggested_asin"] = asin
        else:
            ean = self._get_ean_for_payload()
            if ean:
                attrs["external_product_id"] = ean
                attrs["external_product_id_type"] = "EAN"
        return attrs

    def build_content_attributes(self) -> Dict:
        lang = (
            self.view.remote_languages.first().local_instance
            if self.view.remote_languages.exists()
            else self.sales_channel.multi_tenant_company.language
        )

        translation = (
            ProductTranslation.objects.filter(
                product=self.local_instance,
                language=lang,
                sales_channel=self.sales_channel,
            ).first()
            or ProductTranslation.objects.filter(
                product=self.local_instance,
                language=lang,
                sales_channel=None,
            ).first()
        )

        if not translation:
            return {}

        bullet_points = list(
            ProductTranslationBulletPoint.objects.filter(
                product_translation=translation
            ).order_by("sort_order").values_list("text", flat=True)
        )

        attrs = {
            "item_name": translation.name,
            "product_description": translation.description,
        }
        if bullet_points:
            attrs["bullet_point"] = bullet_points
        return attrs

    def build_price_attributes(self) -> Dict:
        attrs: Dict = {}
        if not self.sales_channel.sync_prices:
            return attrs

        currencies = AmazonCurrency.objects.filter(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
        ).select_related("local_instance")

        for rc in currencies:
            iso = rc.local_instance.iso_code
            full, discount = self.local_instance.get_price_for_sales_channel(
                self.sales_channel, currency=rc.local_instance
            )
            list_price = discount or full
            if list_price is None:
                continue
            attrs.setdefault("list_price", []).append({"currency": iso, "amount": float(list_price)})
            if full is not None:
                attrs.setdefault("uvp_list_price", []).append({"currency": iso, "amount": float(full)})

        return attrs

    # ------------------------------------------------------------
    # Property handling
    # ------------------------------------------------------------
    def process_single_property(self, product_property):
        try:
            remote_property = self.remote_product_property_class.objects.get(
                local_instance=product_property,
                remote_product=self.remote_instance,
                sales_channel=self.sales_channel,
            )

            fac = AmazonProductPropertyUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=product_property,
                remote_product=self.remote_instance,
                remote_instance=remote_property,
                view=self.view,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            fac.run()

            if remote_property.needs_update(fac.remote_value):
                remote_property.remote_value = fac.remote_value
                remote_property.save()

            self.remote_product_properties.append(remote_property)
            data = json.loads(fac.remote_value or "{}")
            self.attributes.update(data)
            return remote_property.id

        except self.remote_product_property_class.DoesNotExist:
            create_fac = AmazonProductPropertyCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=product_property,
                remote_product=self.remote_instance,
                view=self.view,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            create_fac.run()

            self.remote_product_properties.append(create_fac.remote_instance)
            data = json.loads(create_fac.remote_value or "{}")
            self.attributes.update(data)
            return create_fac.remote_instance.id


    def build_payload(self):
        super().build_payload()
        # gather image attributes before building payload so they are sent with the product
        self.assign_images()
        self.attributes.update(self.build_basic_attributes())
        self.attributes.update(self.build_content_attributes())
        self.attributes.update(self.build_price_attributes())
        self.attributes.update(self.image_attributes)

        self.payload = {
            "productType": self.remote_type,
            "requirements": "LISTING",
            "attributes": self.attributes,
        }

    def process_content_translation(self, short_description, description, url_key, remote_language):
        fac = AmazonProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_instance,
            view=self.view,
            api=self.api,
            skip_checks=True,
            language=remote_language.local_instance,
        )
        fac.run()

    # ------------------------------------------------------------
    # Remote helpers
    # ------------------------------------------------------------
    def get_saleschannel_remote_object(self, sku):
        listings = ListingsApi(self._get_client())
        try:
            resp = listings.get_listings_item(
                seller_id=self.sales_channel.remote_id,
                sku=sku,
                marketplace_ids=[self.view.remote_id],
            )
            return resp.payload
        except Exception:
            return None

    # ------------------------------------------------------------
    # Image assignments
    # ------------------------------------------------------------
    def create_image_assignment(self, media_through):
        factory = self.remote_image_assign_create_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api,
            view=self.view,
            get_value_only=True,
        )
        factory.run()
        self.image_attributes.update(factory.build_body()["attributes"])
        return factory.remote_instance

    def update_image_assignment(self, media_through, remote_image_assoc):
        factory = self.remote_image_assign_update_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            remote_instance=remote_image_assoc,
            skip_checks=True,
            remote_product=self.remote_instance,
            api=self.api,
            view=self.view,
            get_value_only=True,
        )
        factory.run()
        self.image_attributes.update(factory.build_body()["attributes"])
        return factory.remote_instance

    def delete_image_assignment(self, media_through, remote_image_assoc):
        remote_image_assoc.delete()
        return True

    def run_create_flow(self):
        """
        Method to create the product if it was not created when we tried to sync it
        """
        if self.create_product_factory is None:
            raise ValueError("create_product_factory must be specified in the RemoteProductSyncFactory.")

        fac = self.create_product_factory(self.sales_channel, self.local_instance, api=self.api, view=self.view)
        fac.run()
        self.remote_instance = fac.remote_instance


class AmazonProductUpdateFactory(AmazonProductBaseFactory, RemoteProductUpdateFactory):
    fixing_identifier_class = AmazonProductBaseFactory

    def perform_remote_action(self):
        listings = ListingsApi(self._get_client())
        resp = listings.patch_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=self.remote_instance.remote_sku,
            marketplace_ids=[self.view.remote_id],
            body=self.payload,
        )
        self.update_assign_issues(getattr(resp, "issues", []))
        return resp

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else True


class AmazonProductCreateFactory(AmazonProductBaseFactory, RemoteProductCreateFactory):
    remote_id_map = "sku"
    fixing_identifier_class = AmazonProductBaseFactory
    remote_product_content_class = None
    remote_price_class = None
    remote_product_eancode_class = None

    def perform_remote_action(self):
        listings = ListingsApi(self._get_client())
        resp = listings.put_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=self.remote_instance.remote_sku,
            marketplace_ids=[self.view.remote_id],
            body=self.payload,
        )
        self.update_assign_issues(getattr(resp, "issues", []))
        return resp

    def post_action_process(self):
        if self.view.remote_id not in (self.remote_instance.created_marketplaces or []):
            self.remote_instance.created_marketplaces.append(self.view.remote_id)
            if not self.remote_instance.ean_code:
                self.remote_instance.ean_code = self._get_ean_for_payload()
            self.remote_instance.save(update_fields=["created_marketplaces", "ean_code"])

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else True


class AmazonProductSyncFactory(AmazonProductBaseFactory, RemoteProductSyncFactory):
    """Sync Amazon products using marketplace-specific create or update."""
    create_product_factory = AmazonProductCreateFactory

class AmazonProductDeleteFactory(GetAmazonAPIMixin, RemoteProductDeleteFactory):
    remote_model_class = AmazonProduct
    delete_remote_instance = True

    def delete_remote(self):
        listings = ListingsApi(self._get_client())
        try:
            resp = listings.delete_listings_item(
                seller_id=self.sales_channel.remote_id,
                sku=self.remote_instance.remote_sku,
                marketplace_ids=[self.view.remote_id],
            )
            return resp
        except Exception as e:
            logger.error("Amazon delete failed: %s", e)
            return True

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else True
