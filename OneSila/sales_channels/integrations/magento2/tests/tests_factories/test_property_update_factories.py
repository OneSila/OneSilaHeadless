from unittest.mock import MagicMock, patch

from model_bakery import baker

from core.tests import TransactionTestCase
from properties.models import Property, PropertySelectValue
from sales_channels.integrations.magento2.factories.properties.properties import (
    MagentoPropertySelectValueUpdateFactory,
    MagentoPropertyUpdateFactory,
)
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.models.properties import (
    MagentoProperty,
    MagentoPropertySelectValue,
)
from sales_channels import signals as sc_signals


class MagentoPropertyUpdateFactoryTests(TransactionTestCase):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._connect_patcher = patch.object(
            MagentoSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )

    def test_property_update_applies_payload_and_saves(self, *, _unused=None):
        local_property = baker.make(
            Property,
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_property = MagentoProperty.objects.create(
            sales_channel=self.sales_channel,
            local_instance=local_property,
            attribute_code="color",
            multi_tenant_company=self.multi_tenant_company,
        )

        api = MagicMock()
        magento_instance = MagicMock()
        api.product_attributes.by_code.return_value = magento_instance

        factory = MagentoPropertyUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=local_property,
            remote_instance=remote_property,
            api=api,
        )
        factory.payload = {
            "is_filterable": True,
            "default_frontend_label": "Color",
        }

        factory.update_remote()

        api.product_attributes.by_code.assert_called_once_with("color")
        self.assertEqual(magento_instance.is_filterable, True)
        self.assertEqual(magento_instance.default_frontend_label, "Color")
        magento_instance.save.assert_called_once()

    def test_select_value_update_applies_payload_and_saves(self, *, _unused=None):
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
        remote_property = MagentoProperty.objects.create(
            sales_channel=self.sales_channel,
            local_instance=local_property,
            attribute_code="color",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_value = MagentoPropertySelectValue.objects.create(
            sales_channel=self.sales_channel,
            local_instance=local_value,
            remote_property=remote_property,
            remote_id="123",
            multi_tenant_company=self.multi_tenant_company,
        )

        api = MagicMock()
        magento_instance = MagicMock()
        api.product_attribute_options.by_id.return_value = magento_instance

        factory = MagentoPropertySelectValueUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=local_value,
            remote_instance=remote_value,
            api=api,
        )
        factory.payload = {
            "label": "Red",
            "store_labels": [{"label": "Red", "store_id": 1}],
        }

        factory.update_remote()

        api.product_attribute_options.by_id.assert_called_once_with("123")
        self.assertEqual(magento_instance.label, "Red")
        self.assertEqual(
            magento_instance.store_labels,
            [{"label": "Red", "store_id": 1}],
        )
        magento_instance.save.assert_called_once()
