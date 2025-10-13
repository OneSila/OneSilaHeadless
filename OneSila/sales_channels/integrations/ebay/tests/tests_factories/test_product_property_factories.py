from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

from sales_channels.integrations.ebay.factories.products.properties import (
    EbayProductPropertyUpdateFactory,
)
from sales_channels.integrations.ebay.models.properties import EbayProductProperty
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
