import json
from model_bakery import baker
from core.tests import TestCase
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
    ProductPropertiesRule,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import AmazonProduct
from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonPublicDefinition,
    AmazonProductType,
    AmazonProductProperty,
)
from sales_channels.integrations.amazon.factories.properties import (
    AmazonProductPropertyCreateFactory,
    AmazonProductPropertyUpdateFactory,
)


class AmazonProductPropertyFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
        )
        self.view = AmazonSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        AmazonRemoteLanguage.objects.create(
            sales_channel_view=self.view, remote_code="en"
        )

        # Create product type property and value
        self.product_type_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            is_product_type=True,
            internal_name="category",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
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
            property_select_value=self.product_type_value,
            language=self.multi_tenant_company.language,
            value="Chair",
        )
        self.rule = ProductPropertiesRule.objects.create(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Create product
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Color property and value
        self.color_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="color",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=self.color_property,
            language=self.multi_tenant_company.language,
            name="Color",
        )
        self.color_value = baker.make(
            PropertySelectValue,
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            property_select_value=self.color_value,
            language=self.multi_tenant_company.language,
            value="Red",
        )
        self.product_property = ProductProperty.objects.create(
            product=self.product,
            property=self.color_property,
            value_select=self.color_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Remote product
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

        # Amazon mapping
        self.amazon_property = AmazonProperty.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.color_property,
            code="color",
            main_code="color",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )
        self.amazon_product_type = AmazonProductType.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )
        self.public_definition = AmazonPublicDefinition.objects.create(
            api_region_code="EU_UK",
            product_type_code="CHAIR",
            code="color",
            name="Color",
            usage_definition=json.dumps(
                {
                    "color": [
                        {
                            "value": "%value:color%",
                            "language_tag": "%auto:language%",
                            "marketplace_id": "%auto:marketplace_id%",
                        }
                    ]
                }
            ),
        )

    def test_create_factory_value_only(self):
        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
        )
        body = fac.create_body()
        self.assertIsNone(body)
        expected = {
            "color": [
                {
                    "value": "Red",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ]
        }
        self.assertEqual(json.loads(fac.remote_value), expected)

    def test_update_factory_value_only(self):
        remote_instance = AmazonProductProperty.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            remote_property=self.amazon_property,
            remote_value="{}",
        )
        fac = AmazonProductPropertyUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            remote_instance=remote_instance,
            get_value_only=True,
        )
        needs_update = fac.additional_update_check()
        self.assertFalse(needs_update)
        expected = {
            "color": [
                {
                    "value": "Red",
                    "language_tag": "en",
                    "marketplace_id": "GB",
                }
            ]
        }
        remote_instance.refresh_from_db()
        self.assertEqual(json.loads(remote_instance.remote_value), expected)

    def test_create_factory_property_not_mapped(self):
        size_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="size",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=size_property,
            language=self.multi_tenant_company.language,
            name="Size",
        )
        size_value = baker.make(
            PropertySelectValue,
            property=size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            property_select_value=size_value,
            language=self.multi_tenant_company.language,
            value="Large",
        )
        prop_instance = ProductProperty.objects.create(
            product=self.product,
            property=size_property,
            value_select=size_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=prop_instance,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
        )

        with self.assertRaises(AmazonProperty.DoesNotExist):
            fac.create_body()

    def test_create_factory_rule_not_mapped(self):
        self.amazon_product_type.delete()
        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
        )

        with self.assertRaises(AmazonProductType.DoesNotExist):
            fac.create_body()

    def test_create_factory_unmapped_select_value(self):
        self.amazon_property.allows_unmapped_values = False
        self.amazon_property.save()

        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=True,
        )

        with self.assertRaises(ValueError):
            fac.create_body()

