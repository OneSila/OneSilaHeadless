from __future__ import annotations

import json
from datetime import date, datetime
from types import SimpleNamespace

from model_bakery import baker

from core.tests import TestCase
from products.models import Product
from properties.models import (
    ProductPropertiesRule,
    ProductProperty,
    ProductPropertyTextTranslation,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.amazon.factories.properties.mixins import AmazonProductPropertyBaseMixin
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.models.properties import (
    AmazonProductType,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonPublicDefinition,
)
from sales_channels.integrations.amazon.models.sales_channels import AmazonSalesChannelView
from sales_channels.integrations.ebay.factories.products.mixins import EbayInventoryItemPayloadMixin
from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView
from sales_channels.integrations.ebay.models.properties import EbayProperty, EbayPropertySelectValue
from sales_channels.integrations.magento2.factories.mixins import MagentoRemoteValueMixin
from sales_channels.integrations.magento2.models import MagentoProperty, MagentoSalesChannel
from sales_channels.integrations.shein.factories.properties.properties import SheinProductPropertyValueMixin
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.models.properties import (
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
)
from sales_channels.integrations.shopify.factories.mixins import ShopifyRemoteValueMixin
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.woocommerce.factories.mixins import WoocommerceRemoteValueConversionMixin
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute, WoocommerceSalesChannel
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


TARGET_TYPES = [
    Property.TYPES.INT,
    Property.TYPES.FLOAT,
    Property.TYPES.TEXT,
    Property.TYPES.DESCRIPTION,
    Property.TYPES.BOOLEAN,
    Property.TYPES.DATE,
    Property.TYPES.DATETIME,
    Property.TYPES.SELECT,
    Property.TYPES.MULTISELECT,
]


def _original_type_from_key(*, original_key):
    if original_key.startswith("SELECT__"):
        return Property.TYPES.SELECT
    if original_key.startswith("MULTISELECT__"):
        return Property.TYPES.MULTISELECT
    return original_key


def _allows_unmapped_from_key(*, original_key):
    if original_key.endswith("not_allows_custom_values"):
        return False
    if original_key.endswith("allows_custom_values"):
        return True
    return False


class _AmazonPayloadRunner(AmazonProductPropertyBaseMixin):
    def __init__(self, *, sales_channel, view, local_instance, remote_property):
        self.sales_channel = sales_channel
        self.view = view
        self.local_instance = local_instance
        self.remote_property = remote_property
        self.remote_product = SimpleNamespace(product_owner=False)
        self.get_value_only = True


class _EbayPayloadRunner(EbayInventoryItemPayloadMixin):
    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel

    def _get_language_code(self):
        return "en"


class _SheinPayloadRunner(SheinProductPropertyValueMixin):
    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel
        self.language = "en"
        self.create_remote_custom_values = False


class _MagentoValueRunner(MagentoRemoteValueMixin):
    def __init__(self, *, sales_channel, local_instance):
        self.sales_channel = sales_channel
        self.local_instance = local_instance
        self.local_property = local_instance.property
        self.get_value_only = False
        self.language = None
        self.remote_select_values = ["101", "102"]


class _WooValueRunner(WoocommerceRemoteValueConversionMixin):
    def __init__(self, *, local_instance):
        self.local_instance = local_instance
        self.local_property = local_instance.property


class _ShopifyValueRunner(ShopifyRemoteValueMixin):
    def __init__(self, *, local_instance):
        self.local_instance = local_instance
        self.local_property = local_instance.property


class BaseRemotePropertyTypeCase(DisableMagentoAndWooConnectionsMixin, TestCase):
    ORIGINAL_KEY = None
    INCLUDE_MANAGED_INTEGRATIONS = True

    def setUp(self):
        super().setUp()
        self._suffix = 0

        self.amazon_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="amazon.matrix.example.com",
        )
        self.amazon_view = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            api_region_code="EU_DE",
            remote_id="A1PA6795UKMFR9",
        )

        self.ebay_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay.matrix.example.com",
        )
        self.ebay_marketplace = baker.make(
            EbaySalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
        )

        self.shein_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.matrix.example.com",
        )

        self.magento_channel = baker.make(
            MagentoSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://magento.matrix.example.com",
        )
        self.woo_channel = baker.make(
            WoocommerceSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://woo.matrix.example.com",
        )
        self.shopify_channel = baker.make(
            ShopifySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="shopify.matrix.example.com",
            access_token="token",
        )

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
            defaults={"type": Property.TYPES.SELECT},
        )
        self.product_type_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        baker.make(
            PropertySelectValueTranslation,
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language="en",
            value="Default Product Type",
        )

        self.amazon_rule = baker.make(
            ProductPropertiesRule,
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
            sales_channel=self.amazon_channel,
        )
        self.amazon_product_type = baker.make(
            AmazonProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            local_instance=self.amazon_rule,
            product_type_code=f"PT-MATRIX-{self._next_suffix()}",
            listing_offer_required_properties={
                self.amazon_view.api_region_code: [],
            },
        )

    def _next_suffix(self):
        self._suffix += 1
        return self._suffix

    def _build_local_product_property(self, *, target_type, value_override=None):
        suffix = self._next_suffix()
        product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku=f"matrix-sku-{suffix}",
        )
        baker.make(
            ProductProperty,
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self.product_type_property,
            value_select=self.product_type_value,
        )

        local_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=target_type,
        )

        select_values = []
        if target_type == Property.TYPES.INT:
            value_int = 42 if value_override is None else value_override
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
                value_int=value_int,
            )
        elif target_type == Property.TYPES.FLOAT:
            value_float = 12.5 if value_override is None else value_override
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
                value_float=value_float,
            )
        elif target_type == Property.TYPES.BOOLEAN:
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
                value_boolean=True,
            )
        elif target_type == Property.TYPES.DATE:
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
                value_date=date(2026, 2, 11),
            )
        elif target_type == Property.TYPES.DATETIME:
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
                value_datetime=datetime(2026, 2, 11, 10, 30, 0),
            )
        elif target_type in (Property.TYPES.TEXT, Property.TYPES.DESCRIPTION):
            text_value = "42" if value_override is None else str(value_override)
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
            )
            baker.make(
                ProductPropertyTextTranslation,
                multi_tenant_company=self.multi_tenant_company,
                product_property=product_property,
                language="en",
                value_text=text_value,
                value_description=text_value,
            )
        elif target_type == Property.TYPES.SELECT:
            select_value = baker.make(
                PropertySelectValue,
                multi_tenant_company=self.multi_tenant_company,
                property=local_property,
            )
            baker.make(
                PropertySelectValueTranslation,
                multi_tenant_company=self.multi_tenant_company,
                propertyselectvalue=select_value,
                language="en",
                value="Option A",
            )
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
                value_select=select_value,
            )
            select_values = [select_value]
        elif target_type == Property.TYPES.MULTISELECT:
            select_value_one = baker.make(
                PropertySelectValue,
                multi_tenant_company=self.multi_tenant_company,
                property=local_property,
            )
            select_value_two = baker.make(
                PropertySelectValue,
                multi_tenant_company=self.multi_tenant_company,
                property=local_property,
            )
            baker.make(
                PropertySelectValueTranslation,
                multi_tenant_company=self.multi_tenant_company,
                propertyselectvalue=select_value_one,
                language="en",
                value="Option A",
            )
            baker.make(
                PropertySelectValueTranslation,
                multi_tenant_company=self.multi_tenant_company,
                propertyselectvalue=select_value_two,
                language="en",
                value="Option B",
            )
            product_property = baker.make(
                ProductProperty,
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=local_property,
            )
            product_property.value_multi_select.set([select_value_one, select_value_two])
            select_values = [select_value_one, select_value_two]
        else:
            raise AssertionError(f"Unsupported target type: {target_type}")

        return product_property, select_values

    def _build_amazon_property(self, *, local_property, original_type, target_type, allows_unmapped):
        suffix = self._next_suffix()
        return baker.prepare(
            AmazonProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.amazon_channel,
            local_instance=local_property,
            code=f"matrix_amazon_{suffix}",
            original_type=original_type,
            type=target_type,
            allows_unmapped_values=allows_unmapped,
        )

    def _build_ebay_property(self, *, local_property, original_type, target_type, allows_unmapped):
        suffix = self._next_suffix()
        return baker.prepare(
            EbayProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.ebay_channel,
            marketplace=self.ebay_marketplace,
            local_instance=local_property,
            localized_name=f"matrix_ebay_{suffix}",
            translated_name=f"matrix_ebay_t_{suffix}",
            original_type=original_type,
            type=target_type,
            allows_unmapped_values=allows_unmapped,
        )

    def _build_shein_property(self, *, local_property, original_type, target_type, allows_unmapped):
        suffix = self._next_suffix()
        return baker.prepare(
            SheinProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            local_instance=local_property,
            name=f"matrix_shein_{suffix}",
            name_en=f"matrix_shein_en_{suffix}",
            remote_id=str(1000 + suffix),
            original_type=original_type,
            type=target_type,
            allows_unmapped_values=allows_unmapped,
        )

    def _build_magento_property(self, *, local_property, original_type, target_type):
        suffix = self._next_suffix()
        return baker.prepare(
            MagentoProperty,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.magento_channel,
            local_instance=local_property,
            attribute_code=f"matrix_magento_{suffix}",
            original_type=original_type,
            type=target_type,
            allows_unmapped_values=True,
        )

    def _build_woo_property(self, *, local_property, original_type, target_type):
        return baker.prepare(
            WoocommerceGlobalAttribute,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.woo_channel,
            local_instance=local_property,
            original_type=original_type,
            type=target_type,
            allows_unmapped_values=True,
        )

    def _persist_remote_property_for_payload_asserts(
        self,
        *,
        remote_property,
        original_type,
        target_type,
        allows_unmapped,
    ):
        # Persist with a save-compatible state first, then patch desired matrix state in DB.
        remote_property.original_type = target_type
        remote_property.type = target_type
        remote_property.allows_unmapped_values = allows_unmapped
        remote_property.save()

        remote_property.__class__.objects.filter(pk=remote_property.pk).update(
            original_type=original_type,
            type=target_type,
            allows_unmapped_values=allows_unmapped,
        )
        remote_property.original_type = original_type
        remote_property.type = target_type
        remote_property.allows_unmapped_values = allows_unmapped

    def _create_select_value_mappings(self, *, target_type, select_values, amazon_property, ebay_property, shein_property):
        if target_type not in (Property.TYPES.SELECT, Property.TYPES.MULTISELECT):
            return

        for idx, select_value in enumerate(select_values, start=1):
            baker.make(
                AmazonPropertySelectValue,
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.amazon_channel,
                amazon_property=amazon_property,
                marketplace=self.amazon_view,
                local_instance=select_value,
                remote_value=f"amazon-{idx}",
                remote_name=f"Amazon Option {idx}",
            )
            baker.make(
                EbayPropertySelectValue,
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.ebay_channel,
                ebay_property=ebay_property,
                marketplace=self.ebay_marketplace,
                local_instance=select_value,
                localized_value=f"ebay-{idx}",
                translated_value=f"Ebay Option {idx}",
            )
            baker.make(
                SheinPropertySelectValue,
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.shein_channel,
                remote_property=shein_property,
                local_instance=select_value,
                remote_id=str(2000 + idx),
                value=f"shein-{idx}",
                value_en=f"Shein Option {idx}",
            )

    def _print_assert_payload(self, *, integration, payload, expected):
        print(f"\\n[{integration}]")
        print(self._format_payload_debug(payload, expected))

    def _assert_amazon_payload(self, *, product_property, amazon_property):
        current_listing_map = dict(self.amazon_product_type.listing_offer_required_properties or {})
        allowed_properties = list(current_listing_map.get(self.amazon_view.api_region_code, []))
        if amazon_property.main_code not in allowed_properties:
            allowed_properties.append(amazon_property.main_code)
        current_listing_map[self.amazon_view.api_region_code] = allowed_properties
        self.amazon_product_type.listing_offer_required_properties = current_listing_map
        self.amazon_product_type.save(update_fields=["listing_offer_required_properties"])

        public_def, _ = AmazonPublicDefinition.objects.get_or_create(
            api_region_code=self.amazon_view.api_region_code,
            product_type_code=self.amazon_product_type.product_type_code,
            code=amazon_property.main_code,
            defaults={
                "name": amazon_property.name or amazon_property.code,
                "usage_definition": json.dumps({"value": f"%value:{amazon_property.code}%"}),
            },
        )
        if public_def.usage_definition != json.dumps({"value": f"%value:{amazon_property.code}%"}):
            public_def.usage_definition = json.dumps({"value": f"%value:{amazon_property.code}%"})
            public_def.save(update_fields=["usage_definition"])

        runner = _AmazonPayloadRunner(
            sales_channel=self.amazon_channel,
            view=self.amazon_view,
            local_instance=product_property,
            remote_property=amazon_property,
        )
        _, payload = runner.build_payload()
        expected = {"type": "dict", "contains_key": "value"}
        self._print_assert_payload(
            integration="AMAZON",
            payload=payload,
            expected=expected,
        )
        self.assertIsInstance(payload, dict, self._format_payload_debug(payload, expected))
        self.assertIn("value", payload, self._format_payload_debug(payload, expected))

    def _assert_ebay_payload(self, *, product_property, ebay_property):
        runner = _EbayPayloadRunner(sales_channel=self.ebay_channel)
        remote_value = runner._prepare_property_remote_value(
            product_property=product_property,
            remote_property=ebay_property,
        )
        expected = {"type": "str"}
        self._print_assert_payload(
            integration="EBAY",
            payload=remote_value,
            expected=expected,
        )
        self.assertIsInstance(remote_value, str, self._format_payload_debug(remote_value, expected))

    def _assert_shein_payload(self, *, product_property, shein_property):
        product_type = baker.make(
            SheinProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            remote_id=str(3000 + self._next_suffix()),
            category_id=str(4000 + self._next_suffix()),
            name="Matrix Product Type",
        )
        product_type_item = baker.make(
            SheinProductTypeItem,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.shein_channel,
            product_type=product_type,
            property=shein_property,
            allows_unmapped_values=shein_property.allows_unmapped_values,
            attribute_type=SheinProductTypeItem.AttributeType.COMMON,
        )

        runner = _SheinPayloadRunner(sales_channel=self.shein_channel)
        payload = runner._build_remote_value(
            product_property=product_property,
            product_type_item=product_type_item,
        )
        expected = {"type": "dict", "contains_key": "attribute_id"}
        self._print_assert_payload(
            integration="SHEIN",
            payload=payload,
            expected=expected,
        )
        self.assertIsInstance(payload, dict, self._format_payload_debug(payload, expected))
        self.assertIn("attribute_id", payload, self._format_payload_debug(payload, expected))

    def _assert_magento_payload(self, *, product_property, remote_property=None):
        runner = _MagentoValueRunner(
            sales_channel=self.magento_channel,
            local_instance=product_property,
        )
        value = runner.get_remote_value(
            product_property=product_property,
            remote_property=remote_property,
        )
        expected = {"not_none": True}
        self._print_assert_payload(
            integration="MAGENTO",
            payload=value,
            expected=expected,
        )
        self.assertIsNotNone(value, self._format_payload_debug(value, expected))

    def _assert_woo_payload(self, *, product_property, remote_property=None):
        runner = _WooValueRunner(local_instance=product_property)
        value = runner.get_remote_value(
            product_property=product_property,
            remote_property=remote_property,
        )
        expected = {"not_none": True}
        self._print_assert_payload(
            integration="WOO",
            payload=value,
            expected=expected,
        )
        self.assertIsNotNone(value, self._format_payload_debug(value, expected))

    def _assert_shopify_payload(self, *, product_property, remote_property=None):
        _ = self.shopify_channel
        runner = _ShopifyValueRunner(local_instance=product_property)
        value = runner.get_remote_value(
            product_property=product_property,
            remote_property=remote_property,
        )
        expected = {"not_none": True}
        self._print_assert_payload(
            integration="SHOPIFY",
            payload=value,
            expected=expected,
        )
        self.assertIsNotNone(value, self._format_payload_debug(value, expected))

    def _assert_payload_acceptance(self, *, accepted, assertion_callable):
        if accepted:
            assertion_callable()
            return
        with self.assertRaises(PreFlightCheckError):
            assertion_callable()

    def _run_case(
        self,
        *,
        target_type,
        value_override=None,
        amazon_accepted=None,
        ebay_accepted=None,
        shein_accepted=None,
        magento_accepted=None,
        woo_accepted=None,
        shopify_accepted=None,
    ):
        original_key = self.ORIGINAL_KEY
        if amazon_accepted is None:
            amazon_accepted = True
        if ebay_accepted is None:
            ebay_accepted = True
        if shein_accepted is None:
            shein_accepted = True
        if magento_accepted is None:
            magento_accepted = True
        if woo_accepted is None:
            woo_accepted = True
        if shopify_accepted is None:
            shopify_accepted = True

        product_property, select_values = self._build_local_product_property(
            target_type=target_type,
            value_override=value_override,
        )
        local_property = product_property.property

        original_type = _original_type_from_key(original_key=original_key)
        allows_unmapped = _allows_unmapped_from_key(original_key=original_key)

        amazon_property = self._build_amazon_property(
            local_property=local_property,
            original_type=original_type,
            target_type=target_type,
            allows_unmapped=allows_unmapped,
        )
        ebay_property = self._build_ebay_property(
            local_property=local_property,
            original_type=original_type,
            target_type=target_type,
            allows_unmapped=allows_unmapped,
        )
        shein_property = self._build_shein_property(
            local_property=local_property,
            original_type=original_type,
            target_type=target_type,
            allows_unmapped=allows_unmapped,
        )

        self._persist_remote_property_for_payload_asserts(
            remote_property=amazon_property,
            original_type=original_type,
            target_type=target_type,
            allows_unmapped=allows_unmapped,
        )
        self._persist_remote_property_for_payload_asserts(
            remote_property=ebay_property,
            original_type=original_type,
            target_type=target_type,
            allows_unmapped=allows_unmapped,
        )
        self._persist_remote_property_for_payload_asserts(
            remote_property=shein_property,
            original_type=original_type,
            target_type=target_type,
            allows_unmapped=allows_unmapped,
        )

        self._create_select_value_mappings(
            target_type=target_type,
            select_values=select_values,
            amazon_property=amazon_property,
            ebay_property=ebay_property,
            shein_property=shein_property,
        )

        self._assert_payload_acceptance(
            accepted=amazon_accepted,
            assertion_callable=lambda: self._assert_amazon_payload(
                product_property=product_property,
                amazon_property=amazon_property,
            ),
        )
        self._assert_payload_acceptance(
            accepted=ebay_accepted,
            assertion_callable=lambda: self._assert_ebay_payload(
                product_property=product_property,
                ebay_property=ebay_property,
            ),
        )
        self._assert_payload_acceptance(
            accepted=shein_accepted,
            assertion_callable=lambda: self._assert_shein_payload(
                product_property=product_property,
                shein_property=shein_property,
            ),
        )

        if self.INCLUDE_MANAGED_INTEGRATIONS:
            magento_property = self._build_magento_property(
                local_property=local_property,
                original_type=original_type,
                target_type=target_type,
            )
            woo_property = self._build_woo_property(
                local_property=local_property,
                original_type=original_type,
                target_type=target_type,
            )
            shopify_remote_property = SimpleNamespace(
                original_type=original_type,
                type=target_type,
                allows_unmapped_values=True,
                name=getattr(local_property, "name", None),
            )

            self._assert_payload_acceptance(
                accepted=magento_accepted,
                assertion_callable=lambda: self._assert_magento_payload(
                    product_property=product_property,
                    remote_property=magento_property if not magento_accepted else None,
                ),
            )
            self._assert_payload_acceptance(
                accepted=woo_accepted,
                assertion_callable=lambda: self._assert_woo_payload(
                    product_property=product_property,
                    remote_property=woo_property if not woo_accepted else None,
                ),
            )
            self._assert_payload_acceptance(
                accepted=shopify_accepted,
                assertion_callable=lambda: self._assert_shopify_payload(
                    product_property=product_property,
                    remote_property=shopify_remote_property if not shopify_accepted else None,
                ),
            )


class RemotePropertyTypeIntMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.INT

    def test_int_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT, value_override=12)
        self._run_case(
            target_type=Property.TYPES.FLOAT,
            value_override=12.5,
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

    def test_int_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT, value_override="12")
        self._run_case(
            target_type=Property.TYPES.TEXT,
            value_override="12.5",
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

    def test_int_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION, value_override="12")
        self._run_case(
            target_type=Property.TYPES.DESCRIPTION,
            value_override="12.5",
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

    def test_int_to_boolean(self):
        self._run_case(
            target_type=Property.TYPES.BOOLEAN,
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

    def test_int_to_date(self):
        self._run_case(
            target_type=Property.TYPES.DATE,
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

    def test_int_to_datetime(self):
        self._run_case(
            target_type=Property.TYPES.DATETIME,
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

    def test_int_to_select(self):
        # @TODO: Handle original numeric type (INT/FLOAT) remapped to SELECT with explicit option mapping/preflight rules.
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_int_to_multiselect(self):
        self._run_case(
            target_type=Property.TYPES.MULTISELECT,
            amazon_accepted=False,
            ebay_accepted=False,
            shein_accepted=False,
        )

class RemotePropertyTypeFloatMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.FLOAT

    def test_float_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_float_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_float_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_float_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_float_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_float_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_float_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_float_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeTextMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.TEXT

    def test_text_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_text_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_text_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_text_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_text_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_text_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_text_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_text_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeDescriptionMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.DESCRIPTION

    def test_description_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_description_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_description_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_description_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_description_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_description_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_description_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_description_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeBooleanMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.BOOLEAN

    def test_boolean_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_boolean_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_boolean_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_boolean_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_boolean_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_boolean_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_boolean_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_boolean_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeDateMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.DATE

    def test_date_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_date_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_date_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_date_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_date_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_date_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_date_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_date_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeDatetimeMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = Property.TYPES.DATETIME

    def test_datetime_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_datetime_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_datetime_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_datetime_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_datetime_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_datetime_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_datetime_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

    def test_datetime_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeSelectCustomValuesAllowedMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = "SELECT__allows_custom_values"

    def test_select_custom_values_allowed_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_select_custom_values_allowed_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_select_custom_values_allowed_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_select_custom_values_allowed_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_select_custom_values_allowed_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_select_custom_values_allowed_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_select_custom_values_allowed_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_select_custom_values_allowed_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeSelectCustomValuesNotAllowedMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = "SELECT__not_allows_custom_values"
    INCLUDE_MANAGED_INTEGRATIONS = False

    def test_select_custom_values_not_allowed_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_select_custom_values_not_allowed_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_select_custom_values_not_allowed_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_select_custom_values_not_allowed_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_select_custom_values_not_allowed_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_select_custom_values_not_allowed_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_select_custom_values_not_allowed_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_select_custom_values_not_allowed_to_multiselect(self):
        self._run_case(target_type=Property.TYPES.MULTISELECT)

class RemotePropertyTypeMultiselectCustomValuesAllowedMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = "MULTISELECT__allows_custom_values"

    def test_multiselect_custom_values_allowed_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_multiselect_custom_values_allowed_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_multiselect_custom_values_allowed_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_multiselect_custom_values_allowed_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_multiselect_custom_values_allowed_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_multiselect_custom_values_allowed_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_multiselect_custom_values_allowed_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_multiselect_custom_values_allowed_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)

class RemotePropertyTypeMultiselectCustomValuesNotAllowedMatrixTestCase(BaseRemotePropertyTypeCase):
    ORIGINAL_KEY = "MULTISELECT__not_allows_custom_values"
    INCLUDE_MANAGED_INTEGRATIONS = False

    def test_multiselect_custom_values_not_allowed_to_int(self):
        self._run_case(target_type=Property.TYPES.INT)

    def test_multiselect_custom_values_not_allowed_to_float(self):
        self._run_case(target_type=Property.TYPES.FLOAT)

    def test_multiselect_custom_values_not_allowed_to_text(self):
        self._run_case(target_type=Property.TYPES.TEXT)

    def test_multiselect_custom_values_not_allowed_to_description(self):
        self._run_case(target_type=Property.TYPES.DESCRIPTION)

    def test_multiselect_custom_values_not_allowed_to_boolean(self):
        self._run_case(target_type=Property.TYPES.BOOLEAN)

    def test_multiselect_custom_values_not_allowed_to_date(self):
        self._run_case(target_type=Property.TYPES.DATE)

    def test_multiselect_custom_values_not_allowed_to_datetime(self):
        self._run_case(target_type=Property.TYPES.DATETIME)

    def test_multiselect_custom_values_not_allowed_to_select(self):
        self._run_case(target_type=Property.TYPES.SELECT)
