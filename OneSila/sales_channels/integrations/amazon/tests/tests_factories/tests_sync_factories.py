from model_bakery import baker

from core.tests import TestCase
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


class AmazonSyncFactoriesTest(TestCase):
    def setUp(self):
        super().setUp()
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
