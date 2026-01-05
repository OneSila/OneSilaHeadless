from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

from model_bakery import baker

from properties.models import (
    ProductProperty,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.exceptions import RemotePropertyValueNotMapped
from sales_channels.integrations.ebay.exceptions import EbayPropertyMappingMissingError
from sales_channels.integrations.ebay.factories.products.properties import (
    EbayProductPropertyUpdateFactory,
)
from sales_channels.integrations.ebay.models.properties import (
    EbayProductProperty,
    EbayProperty,
    EbayPropertySelectValue,
)
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    EbayProductPushFactoryTestBase,
)


class EbayProductPropertyUpdateFactoryTest(EbayProductPushFactoryTestBase):
    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPushMixin.get_api",
        return_value=MagicMock(),
    )
    @patch.object(EbayProductProperty, "has_errors", new_callable=PropertyMock, return_value=False)
    def test_get_value_only_sets_remote_value(
        self,
        _mock_has_errors: PropertyMock,
        _mock_get_api: MagicMock,
        _mock_collect_images,
    ):
        remote_property_instance = EbayProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.brand_product_property,
            remote_product=self.remote_product,
            remote_property=self.remote_brand,
            remote_value="",
        )

        factory = EbayProductPropertyUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.brand_product_property,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
            remote_instance=remote_property_instance,
        )
        factory.log_action = MagicMock()
        factory.log_error = MagicMock()
        factory.run()

        remote_property_instance.refresh_from_db()
        self.assertEqual(remote_property_instance.remote_value, "Acme")

    def test_select_value_creates_custom_mapping_when_allowed(self) -> None:
        self.multi_tenant_company.language = "de"
        self.multi_tenant_company.save(update_fields=["language"])

        local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        local_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=local_value,
            language="en-us",
            value="Red",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=local_value,
            language="de",
            value="Rot",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=local_property,
            value_select=local_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        remote_property = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_property,
            localized_name="Color",
            allows_unmapped_values=True,
        )
        remote_property_instance = EbayProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=remote_property,
            remote_value="",
        )

        factory = EbayProductPropertyUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
            remote_instance=remote_property_instance,
        )
        factory.log_action = MagicMock()
        factory.log_error = MagicMock()
        factory.run()

        remote_value = EbayPropertySelectValue.objects.get(
            sales_channel=self.sales_channel,
            marketplace=self.view,
            ebay_property=remote_property,
            local_instance=local_value,
        )
        self.assertEqual(remote_value.localized_value, "Red")
        self.assertEqual(remote_value.translated_value, "Rot")

        remote_property_instance.refresh_from_db()
        self.assertEqual(remote_property_instance.remote_value, "Red")

    def test_multiselect_unmapped_raises_when_custom_disallowed(self) -> None:
        local_property = baker.make(
            Property,
            type=Property.TYPES.MULTISELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        first_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        second_value = baker.make(
            PropertySelectValue,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=first_value,
            language="en-us",
            value="One",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=second_value,
            language="en-us",
            value="Two",
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property = ProductProperty.objects.create(
            product=self.product,
            property=local_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        product_property.value_multi_select.set([first_value, second_value])

        remote_property = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_property,
            localized_name="Numbers",
            allows_unmapped_values=False,
        )
        remote_property_instance = EbayProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            remote_property=remote_property,
            remote_value="",
        )

        factory = EbayProductPropertyUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
            remote_instance=remote_property_instance,
        )
        factory.log_action = MagicMock()
        factory.log_error = MagicMock()

        with self.assertRaises(RemotePropertyValueNotMapped):
            factory.run()
