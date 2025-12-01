from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from model_bakery import baker

from properties.models import (
    ProductPropertiesRule,
    Property,
    PropertySelectValue,
)
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.shein.factories.sync import (
    SheinSalesChannelMappingSyncFactory,
)
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductType,
    SheinProperty,
    SheinPropertySelectValue,
    SheinSalesChannel,
)


class SheinSalesChannelMappingSyncFactoryTest(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)

        self.source_sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="source.shein.test",
            remote_id="SRC-123",
        )
        self.target_sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="target.shein.test",
            remote_id="TGT-123",
        )

        self.product_type_property = Property.objects.filter(
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        ).first()
        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.rule = ProductPropertiesRule.objects.get(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.local_select_value = baker.make(
            PropertySelectValue,
            property=self.local_property,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_preflight_requires_same_company(self):
        other_company = baker.make("core.MultiTenantCompany")
        other_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=other_company,
            hostname="other.shein.test",
            remote_id="OTHER",
        )

        factory = SheinSalesChannelMappingSyncFactory(
            source_sales_channel=other_channel,
            target_sales_channel=self.target_sales_channel,
        )
        with self.assertRaises(PreFlightCheckError):
            factory.run()

    def test_syncs_product_types_by_remote_id(self):
        SheinProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            remote_id="PT-100",
            local_instance=self.rule,
        )
        target_type = SheinProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            remote_id="PT-100",
        )

        result = SheinSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_type.refresh_from_db()
        self.assertEqual(result["product_types"], 1)
        self.assertEqual(target_type.local_instance, self.rule)

    def test_syncs_properties_by_remote_id(self):
        SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            remote_id="color",
            local_instance=self.local_property,
        )
        target_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            remote_id="color",
        )

        result = SheinSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_property.refresh_from_db()
        self.assertEqual(result["properties"], 1)
        self.assertEqual(target_property.local_instance, self.local_property)

    def test_syncs_select_values_by_remote_id_and_property(self):
        source_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            remote_id="material",
            local_instance=self.local_property,
        )
        target_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            remote_id="material",
            local_instance=self.local_property,
        )
        SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            remote_property=source_property,
            remote_id="leather",
            local_instance=self.local_select_value,
        )
        target_value = SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            remote_property=target_property,
            remote_id="leather",
        )
        unmatched_property = SheinProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            remote_id="style",
        )
        unmatched_value = SheinPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            remote_property=unmatched_property,
            remote_id="leather",
        )

        result = SheinSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_value.refresh_from_db()
        unmatched_value.refresh_from_db()

        self.assertEqual(result["select_values"], 1)
        self.assertEqual(target_value.local_instance, self.local_select_value)
        self.assertIsNone(unmatched_value.local_instance)

    def test_syncs_internal_properties_by_code(self):
        SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            code="brand_code",
            local_instance=self.local_property,
        )
        target_internal = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="brand_code",
        )

        result = SheinSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_internal.refresh_from_db()
        self.assertEqual(result["internal_properties"], 1)
        self.assertEqual(target_internal.local_instance, self.local_property)

    def test_syncs_internal_property_options_by_code_and_value(self):
        source_internal = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            code="brand_code",
            local_instance=self.local_property,
        )
        target_internal = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="brand_code",
            local_instance=self.local_property,
        )
        SheinInternalPropertyOption.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            internal_property=source_internal,
            value="nike",
            label="Nike",
            local_instance=self.local_select_value,
        )
        target_option = SheinInternalPropertyOption.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            internal_property=target_internal,
            value="nike",
            label="Nike",
        )
        other_internal = SheinInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="style_code",
        )
        SheinInternalPropertyOption.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            internal_property=other_internal,
            value="nike",
            label="Nike",
        )

        result = SheinSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_option.refresh_from_db()

        self.assertEqual(result["internal_property_options"], 1)
        self.assertEqual(target_option.local_instance, self.local_select_value)
