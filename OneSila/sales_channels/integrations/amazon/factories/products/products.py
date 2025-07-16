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
from sales_channels.integrations.amazon.exceptions import AmazonUnsupportedPropertyForProductType
from sales_channels.integrations.amazon.factories.mixins import (
    GetAmazonAPIMixin,
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
from sales_channels.integrations.amazon.models.properties import AmazonProductProperty, AmazonProperty, \
    AmazonProductType
from sales_channels.integrations.amazon.models import AmazonCurrency
from sales_channels.exceptions import SwitchedToCreateException, SwitchedToSyncException
from spapi import ListingsApi

import logging

logger = logging.getLogger(__name__)


class AmazonProductBaseFactory(GetAmazonAPIMixin, RemoteProductSyncFactory):
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
        self.prices_data = {}
        self.force_listing_requirements = False

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
        if getattr(self, "remote_instance", None):
            self.force_listing_requirements = getattr(self.remote_instance, "product_owner", False)
        if not hasattr(self, 'current_attrs'):
            self.get_saleschannel_remote_object(self.local_instance.sku)

        if self.is_create and self.view.remote_id in (self.remote_instance.created_marketplaces or []):
            raise SwitchedToSyncException("Listing already created for marketplace")
        if not self.is_create and self.view.remote_id not in (self.remote_instance.created_marketplaces or []):
            raise SwitchedToCreateException("Listing missing for marketplace")

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _get_asin(self) -> str | None:
        asin_property = Property.objects.get(
            internal_name="merchant_suggested_asin",
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

        pp = ProductProperty.objects.filter(product=self.local_instance, property=asin_property).first()
        return pp.get_value() if pp else None

    def _get_ean_for_payload(self) -> str | None:
        return self.remote_instance.ean_code or self.get_ean_code_value()

    def build_basic_attributes(self) -> Dict:
        self.set_sku()

        attrs: Dict = {}
        asin = self._get_asin()
        if asin:
            attrs["merchant_suggested_asin"] = [{"value": asin}]
            self.force_listing_requirements = False
        else:
            ean = self._get_ean_for_payload()
            if ean:
                attrs["externally_assigned_product_identifier"] = [
                    {
                        "type": "ean",
                        "value": ean,
                    }
                ]
                self.force_listing_requirements = True
            else:
                self.force_listing_requirements = False
        return attrs

    def build_content_attributes(self) -> Dict:
        lang = (
            self.view.remote_languages.first().local_instance
            if self.view.remote_languages.exists()
            else self.sales_channel.multi_tenant_company.language
        )

        # Fetch both translations
        channel_translation = ProductTranslation.objects.filter(
            product=self.local_instance,
            language=lang,
            sales_channel=self.sales_channel,
        ).first()

        default_translation = ProductTranslation.objects.filter(
            product=self.local_instance,
            language=lang,
            sales_channel=None,
        ).first()

        # Fallback logic per field
        item_name = None
        product_description = None

        if channel_translation:
            item_name = channel_translation.name or None
            product_description = channel_translation.description or None

        if not item_name and default_translation:
            item_name = default_translation.name

        if not product_description and default_translation:
            product_description = default_translation.description

        # Bullet points ONLY from the channel translation
        bullet_points = []
        if channel_translation:
            bullet_points = list(
                ProductTranslationBulletPoint.objects.filter(
                    product_translation=channel_translation
                ).order_by("sort_order").values_list("text", flat=True)
            )

        attrs = {
            "item_name": [{"value": item_name}],
            "product_description": [{"value": product_description}],
        }

        if bullet_points:
            attrs["bullet_point"] = [{"value": bp} for bp in bullet_points]

        return {k: v for k, v in attrs.items() if v not in (None, "")}

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

            sale_price = discount
            list_price = sale_price if sale_price is not None else full
            if list_price is None:
                continue

            attrs.setdefault("purchasable_offer", []).append(
                {
                    "audience": "ALL",
                    "currency": iso,
                    "marketplace_id": self.view.remote_id,
                    "our_price": [
                        {
                            "schedule": [
                                {"value_with_tax": float(list_price)}
                            ]
                        }
                    ],
                }
            )

            if self.sales_channel.listing_owner or getattr(self.remote_instance, "product_owner", False) or self.force_listing_requirements:
                # @TODO: This can be value_with_tax depending on marketplace use the public definition to get the value
                attrs.setdefault("list_price", []).append(
                    {"currency": iso, "value": float(list_price)}
                )
        return attrs

    def set_rule(self):
        super().set_rule()
        self.remote_rule = AmazonProductType.objects.get(
            local_instance=self.rule,
            sales_channel=self.sales_channel,
        )

    def build_payload(self):
        super().build_payload()
        # gather image attributes before building payload so they are sent with the product
        self.assign_images()
        self.attributes.update(self.build_basic_attributes())
        self.attributes.update(self.build_content_attributes())
        self.attributes.update(self.build_price_attributes())
        self.attributes.update(self.image_attributes)

        self.payload = {
            "productType": self.remote_rule.product_type_code,
            "attributes": self.attributes,
        }

    def process_content_translation(self, short_description, description, url_key, remote_language):
        pass
        # fac = AmazonProductContentUpdateFactory(
        #     sales_channel=self.sales_channel,
        #     local_instance=self.local_instance,
        #     remote_product=self.remote_instance,
        #     view=self.view,
        #     api=self.api,
        #     skip_checks=True,
        #     language=remote_language.local_instance,
        # )
        # fac.run()

    # ------------------------------------------------------------
    # Remote helpers
    # ------------------------------------------------------------
    def get_saleschannel_remote_object(self, sku):
        response = {}
        try:
            response = self.get_listing_item(sku, self.view.remote_id)
        except Exception as e:
            if not self.is_create:
                raise SwitchedToCreateException(f"Product with sku {sku} was not found. Initial error: {str(e)}")

        self.current_attrs = getattr(response, "attributes", {}) or {}
        return response

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

    def run_sync_flow(self):
        """
        Runs the sync/update flow.
        """

        if self.sync_product_factory is None:
            raise ValueError("sync_product_factory must be specified in the RemoteProductCreateFactory.")

        sync_factory = self.sync_product_factory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_instance=self.remote_instance,
            parent_local_instance=self.parent_local_instance,
            remote_parent_product=self.remote_parent_product,
            api=self.api,
            view=self.view
        )
        sync_factory.run()

    def assign_ean_code(self):
        pass  # there is no ean code sync for Amazon. This is used as an identifier and cannot be updated later on

    def set_product_properties(self):
        rule_properties_ids = self.local_instance.get_required_and_optional_properties(product_rule=self.rule).values_list('property_id', flat=True)
        self.product_properties = ProductProperty.objects.filter_multi_tenant(
            self.sales_channel.multi_tenant_company
        ).filter(product=self.local_instance, property_id__in=rule_properties_ids). \
            exclude(property__internal_name='merchant_suggested_asin')

    # ------------------------------------------------------------
    # Property handling
    # ------------------------------------------------------------
    def process_amazon_single_property(self, product_property, remote_property):

        try:
            remote_product_property = self.remote_product_property_class.objects.get(
                local_instance=product_property,
                remote_product=self.remote_instance,
                sales_channel=self.sales_channel,
            )

            fac = AmazonProductPropertyUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=product_property,
                remote_product=self.remote_instance,
                remote_instance=remote_product_property,
                view=self.view,
                remote_property=remote_property,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            fac.run()

            if remote_product_property.needs_update(fac.remote_value):
                remote_product_property.remote_value = fac.remote_value
                remote_product_property.save()

            self.remote_product_properties.append(remote_product_property)
            data = json.loads(fac.remote_value or "{}")
            self.attributes.update(data)
            return remote_product_property.id

        except self.remote_product_property_class.DoesNotExist:
            create_fac = AmazonProductPropertyCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=product_property,
                remote_product=self.remote_instance,
                view=self.view,
                remote_property=remote_property,
                api=self.api,
                get_value_only=True,
                skip_checks=True,
            )
            create_fac.run()

            if hasattr(create_fac, "remote_instance"):
                self.remote_product_properties.append(create_fac.remote_instance)
                data = json.loads(create_fac.remote_value or "{}")
                self.attributes.update(data)

    def process_product_properties(self):
        # We override process_product_properties because:
        # 1. We will not do delete_non_existing_remote_product_property. They will be deleted because are not added to
        # the payload
        # 2. We use process_amazon_single_property that loop through all the remote proprties and call them for that
        # remote property. The reason? In Amazon "size" can be mapped to over 30 amazon properties (ring size, t-shirt size etc)

        for product_property in self.product_properties:

            for remote_property in AmazonProperty.objects.filter(sales_channel=self.sales_channel, local_instance=product_property.property):
                try:
                    self.process_amazon_single_property(product_property, remote_property)
                except AmazonUnsupportedPropertyForProductType:
                    # because we are getting all the properties we might get properties that are not designed for this
                    # product type. We will just skip those
                    pass


class AmazonProductUpdateFactory(AmazonProductBaseFactory, RemoteProductUpdateFactory):
    fixing_identifier_class = AmazonProductBaseFactory

    def perform_remote_action(self):

        resp = self.update_product(
            self.sku,
            self.view.remote_id,
            self.remote_rule,
            self.payload.get("attributes", {}),
            self.current_attrs,
        )
        print('------------------------------------------------------------------------')
        print(resp)
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
        resp = self.create_product(
            sku=self.sku,
            marketplace_id=self.view.remote_id,
            product_type=self.remote_rule,
            attributes=self.payload.get("attributes", {}),
        )
        print('------------------------------------------------------------------------')
        print(resp)

        return resp

    def post_action_process(self):
        if self.view.remote_id not in (self.remote_instance.created_marketplaces or []):
            self.remote_instance.created_marketplaces.append(self.view.remote_id)
            if not self.remote_instance.ean_code:
                self.remote_instance.ean_code = self._get_ean_for_payload()
            update_fields = ["created_marketplaces", "ean_code"]
            if self.force_listing_requirements and not self.remote_instance.product_owner:
                self.remote_instance.product_owner = True
                update_fields.append("product_owner")

            self.remote_instance.save(update_fields=update_fields)

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else True


class AmazonProductSyncFactory(AmazonProductBaseFactory, RemoteProductSyncFactory):
    """Sync Amazon products using marketplace-specific create or update."""
    create_product_factory = AmazonProductCreateFactory

    def _match_amazon_variation_theme(self, configurator):
        themes = self.remote_rule.variation_themes or []
        if not themes:
            return None

        prop_ids = configurator.properties.values_list("id", flat=True)
        codes = list(
            AmazonProperty.objects.filter(
                sales_channel=self.sales_channel,
                local_instance_id__in=prop_ids,
            ).values_list("code", flat=True)
        )
        codes = [c.lower() for c in codes]

        best_theme = None
        best_matches = 0

        for theme in themes:
            parts = [p.lower() for p in theme.split("/")]
            matches = 0
            for part in parts:
                if any(part in code for code in codes):
                    matches += 1
            if matches > best_matches:
                best_matches = matches
                best_theme = theme

        return best_theme

    def set_remote_configurator(self):
        super().set_remote_configurator()

        if not hasattr(self, "configurator"):
            return

        theme = self.configurator.amazon_theme or self._match_amazon_variation_theme(self.configurator)
        if theme and self.configurator.amazon_theme != theme:
            self.configurator.amazon_theme = theme
            self.configurator.save(update_fields=["amazon_theme"])

        self.amazon_theme = self.configurator.amazon_theme

    def build_variation_attributes(self):
        attrs = {}

        theme = None
        configurator = None

        if self.is_variation and self.remote_parent_product and hasattr(self.remote_parent_product, "configurator"):
            configurator = self.remote_parent_product.configurator
        elif self.local_type == Product.CONFIGURABLE and hasattr(self, "configurator"):
            configurator = self.configurator

        if configurator:
            theme = configurator.amazon_theme or self._match_amazon_variation_theme(configurator)

        if theme:
            attrs["variation_theme"] = [{"value": theme, "marketplace_id": self.view.remote_id}]

        if self.is_variation:
            attrs["parentage_level"] = [
                {"value": "child", "marketplace_id": self.view.remote_id}
            ]
            if self.remote_parent_product:
                attrs["child_parent_sku_relationship"] = [
                    {
                        "child_relationship_type": "variation",
                        "parent_sku": self.remote_parent_product.remote_sku,
                        "marketplace_id": self.view.remote_id,
                    }
                ]
        elif self.local_type == Product.CONFIGURABLE:
            attrs["parentage_level"] = [
                {"value": "parent", "marketplace_id": self.view.remote_id}
            ]

        return attrs

    def customize_payload(self):
        self.attributes.update(self.build_variation_attributes())
        self.payload["attributes"] = self.attributes

    def perform_remote_action(self):

        resp = self.update_product(
            self.sku,
            self.view.remote_id,
            self.remote_rule,
            self.payload.get("attributes", {}),
            self.current_attrs,
        )
        print('------------------------------------------------------------------------')
        print(resp)
        return resp

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else True


class AmazonProductDeleteFactory(GetAmazonAPIMixin, RemoteProductDeleteFactory):
    remote_model_class = AmazonProduct
    delete_remote_instance = True

    def __init__(self, *args, view=None, **kwargs):

        if view is None:
            raise ValueError("AmazonProduct factories require a view argument")

        self.view = view
        super().__init__(*args, **kwargs)

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
