from model_bakery import baker
from unittest.mock import PropertyMock, patch

from core.tests import TestCase
from sales_channels.exceptions import PreFlightCheckError
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
)
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
    AmazonDefaultUnitConfigurator,
)
from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
    AmazonProductTypeItem,
)
from sales_channels.integrations.amazon.factories.sync.rule_sync import (
    AmazonPropertyRuleItemSyncFactory,
)
from sales_channels.integrations.amazon.factories.sync.select_value_sync import (
    AmazonPropertySelectValuesSyncFactory,
)
from sales_channels.integrations.amazon.factories.sync.sales_channel_mapping import (
    AmazonSalesChannelMappingSyncFactory,
)


class AmazonSyncFactoriesTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
        )
        self.marketplace_en = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        self.marketplace_de = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="DE",
            api_region_code="EU_DE",
            remote_id="DE",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.marketplace_en,
            remote_code="en",
            local_instance="en",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.marketplace_de,
            remote_code="de",
            local_instance="de",
        )

        # Product type property and rule
        self.product_type_property = Property.objects.filter(
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        ).first()
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
            language=self.multi_tenant_company.language,
            name="Category",
        )
        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language=self.multi_tenant_company.language,
            value="Chair",
        )
        self.rule = ProductPropertiesRule.objects.get(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Local property used in tests
        self.local_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="color",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.local_property,
            language=self.multi_tenant_company.language,
            name="Color",
        )

    def test_property_rule_item_sync_creates_rule_item(self):
        remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_property,
            code="color",
            type=Property.TYPES.SELECT,
        )
        amazon_rule = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )
        AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=amazon_rule,
            remote_property=remote_property,
            remote_type=ProductPropertiesRuleItem.REQUIRED,
        )

        AmazonPropertyRuleItemSyncFactory(remote_property).run()

        rule_item = ProductPropertiesRuleItem.objects.get(
            rule=self.rule,
            property=self.local_property,
        )
        self.assertEqual(rule_item.type, ProductPropertiesRuleItem.REQUIRED)

    def test_property_rule_item_sync_does_not_downgrade(self):
        remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_property,
            code="color",
            type=Property.TYPES.SELECT,
        )
        amazon_rule = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )
        item = AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=amazon_rule,
            remote_property=remote_property,
            remote_type=ProductPropertiesRuleItem.REQUIRED,
        )
        AmazonPropertyRuleItemSyncFactory(remote_property).run()
        rule_item = ProductPropertiesRuleItem.objects.get(
            rule=self.rule,
            property=self.local_property,
        )
        self.assertEqual(rule_item.type, ProductPropertiesRuleItem.REQUIRED)

        # Change remote_type to OPTIONAL and run again
        item.remote_type = ProductPropertiesRuleItem.OPTIONAL
        item.save(update_fields=["remote_type"])
        AmazonPropertyRuleItemSyncFactory(remote_property).run()
        rule_item.refresh_from_db()
        self.assertEqual(rule_item.type, ProductPropertiesRuleItem.REQUIRED)


    def test_property_select_values_sync_maps_duplicates(self):
        remote_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.local_property,
            code="color",
            type=Property.TYPES.SELECT,
        )
        val_en = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=remote_property,
            marketplace=self.marketplace_en,
            remote_value="red",
            remote_name="Red",
        )
        val_de = AmazonPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_property=remote_property,
            marketplace=self.marketplace_de,
            remote_value="red",
            remote_name="Red",
        )
        AmazonPropertySelectValuesSyncFactory(remote_property).run()

        values = PropertySelectValue.objects.filter(property=self.local_property)
        self.assertEqual(values.count(), 1)
        translations = PropertySelectValueTranslation.objects.filter(
            propertyselectvalue=values.first()
        )
        self.assertEqual(translations.count(), 2)
        val_en.refresh_from_db()
        val_de.refresh_from_db()
        self.assertEqual(val_en.local_instance, values.first())
        self.assertEqual(val_de.local_instance, values.first())


class AmazonSalesChannelMappingSyncFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.has_errors_patcher = patch(
            "integrations.models.IntegrationObjectMixin.has_errors",
            new_callable=PropertyMock,
            return_value=False,
        )
        self.has_errors_patcher.start()
        self.addCleanup(self.has_errors_patcher.stop)
        self.source_sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="source.example.com",
            remote_id="SRC123",
        )
        self.target_sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="target.example.com",
            remote_id="TGT123",
        )
        self.source_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            name="Source DE",
            api_region_code="EU_DE",
            remote_id="SRC-DE",
        )
        self.target_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            name="Target DE",
            api_region_code="EU_DE",
            remote_id="TGT-DE",
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
        other_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=other_company,
            hostname="other.example.com",
            remote_id="OTHER",
        )

        factory = AmazonSalesChannelMappingSyncFactory(
            source_sales_channel=other_channel,
            target_sales_channel=self.target_sales_channel,
        )
        with self.assertRaises(PreFlightCheckError):
            factory.run()

    def test_syncs_product_types_by_code(self):
        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            product_type_code="CHAIR",
            local_instance=self.rule,
        )
        target_pt = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            product_type_code="CHAIR",
        )

        result = AmazonSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_pt.refresh_from_db()
        self.assertEqual(result["product_types"], 1)
        self.assertEqual(target_pt.local_instance, self.rule)

    def test_syncs_properties_by_code_and_main_code(self):
        source_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            code="color",
            local_instance=self.local_property,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="color",
        )

        other_local_property = baker.make(
            Property,
            type=Property.TYPES.TEXT,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            code="size__value",
            main_code="size",
            local_instance=other_local_property,
        )
        main_code_target = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="size__width",
            main_code="size",
        )

        result = AmazonSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        main_code_target.refresh_from_db()

        target_color = AmazonProperty.objects.get(
            sales_channel=self.target_sales_channel,
            code="color",
        )

        self.assertEqual(result["properties"], 1)
        self.assertEqual(target_color.local_instance, self.local_property)
        self.assertIsNone(main_code_target.local_instance)

    def test_syncs_select_values_by_remote_value_property_and_region(self):
        source_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            code="material",
            main_code="material",
            local_instance=self.local_property,
        )
        target_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            code="material",
            main_code="material",
            local_instance=self.local_property,
        )
        AmazonPropertySelectValue.objects.bulk_create(
            [
                AmazonPropertySelectValue(
                    multi_tenant_company=self.multi_tenant_company,
                    sales_channel=self.source_sales_channel,
                    amazon_property=source_property,
                    marketplace=self.source_view,
                    remote_value="leather",
                    remote_name="Leather",
                    local_instance=self.local_select_value,
                )
            ]
        )
        other_region_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            name="Target FR",
            api_region_code="EU_FR",
            remote_id="TGT-FR",
        )
        AmazonPropertySelectValue.objects.bulk_create(
            [
                AmazonPropertySelectValue(
                    multi_tenant_company=self.multi_tenant_company,
                    sales_channel=self.target_sales_channel,
                    amazon_property=target_property,
                    marketplace=self.target_view,
                    remote_value="leather",
                    remote_name="Leather",
                ),
                AmazonPropertySelectValue(
                    multi_tenant_company=self.multi_tenant_company,
                    sales_channel=self.target_sales_channel,
                    amazon_property=target_property,
                    marketplace=other_region_view,
                    remote_value="leather",
                    remote_name="Leather",
                ),
            ]
        )

        result = AmazonSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_value = AmazonPropertySelectValue.objects.get(
            sales_channel=self.target_sales_channel,
            marketplace=self.target_view,
            remote_value="leather",
        )
        unmatched_value = AmazonPropertySelectValue.objects.get(
            sales_channel=self.target_sales_channel,
            marketplace=other_region_view,
            remote_value="leather",
        )

        self.assertEqual(result["select_values"], 1)
        self.assertEqual(target_value.local_instance, self.local_select_value)
        self.assertIsNone(unmatched_value.local_instance)

    def test_syncs_default_unit_configurators(self):
        AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.source_sales_channel,
            marketplace=self.source_view,
            name="Weight",
            code="weight",
            selected_unit="kg",
        )
        target_config = AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            marketplace=self.target_view,
            name="Weight",
            code="weight",
        )
        other_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            name="Target FR",
            api_region_code="EU_FR",
            remote_id="TGT-FR",
        )
        AmazonDefaultUnitConfigurator.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.target_sales_channel,
            marketplace=other_view,
            name="Weight",
            code="weight",
        )

        result = AmazonSalesChannelMappingSyncFactory(
            source_sales_channel=self.source_sales_channel,
            target_sales_channel=self.target_sales_channel,
        ).run()

        target_config.refresh_from_db()
        self.assertEqual(result["default_units"], 1)
        self.assertEqual(target_config.selected_unit, "kg")
