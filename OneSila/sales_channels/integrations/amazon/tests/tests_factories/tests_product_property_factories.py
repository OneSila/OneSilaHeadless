import json
from model_bakery import baker
from core.tests import TestCase
from products.models import Product
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
    ProductPropertiesRule, ProductPropertiesRuleItem,
)
from sales_channels.integrations.amazon.factories import AmazonProductSyncFactory
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.models.products import RemoteProductConfigurator
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonProduct,
    AmazonVariationTheme,
)
from sales_channels.integrations.amazon.models import AmazonProductBrowseNode
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


class AmazonProductPropertyTestSetupMixin:
    def prepare_test(self):
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
            listing_owner=True
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view, remote_code="en"
        )

        # Create product type property and value
        self.product_type_property = Property.objects.filter(is_product_type=True,
                                                             multi_tenant_company=self.multi_tenant_company).first()

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
        self.rule = ProductPropertiesRule.objects.filter(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        ).first()

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
            multi_tenant_company=self.multi_tenant_company,
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
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.color_value,
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
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        AmazonProductBrowseNode.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            recommended_browse_node_id="1",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

        # Amazon mapping
        self.amazon_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.color_property,
            code="color",
            main_code="color",
            type=Property.TYPES.SELECT,
            allows_unmapped_values=True,
        )
        self.amazon_product_type = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
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


class AmazonProductPropertyFactoryTest(DisableWooCommerceSignalsMixin, TestCase, AmazonProductPropertyTestSetupMixin):
    def setUp(self):
        super().setUp()
        self.prepare_test()

    def test_product_property_create_factory_value_only(self):
        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            remote_property=self.amazon_property,
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

    def test_product_property_update_factory_value_only(self):
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
            remote_property=self.amazon_property,
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

    def test_product_property_create_factory_rule_not_mapped(self):
        self.amazon_product_type.delete()
        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            remote_property=self.amazon_property,
            get_value_only=True,
        )

        with self.assertRaises(AmazonProductType.DoesNotExist):
            fac.create_body()

    def test_product_property_create_factory_unmapped_select_value(self):
        self.amazon_property.allows_unmapped_values = False
        self.amazon_property.save()

        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            remote_property=self.amazon_property,
            get_value_only=True,
        )

        with self.assertRaises(ValueError):
            fac.create_body()


class AmazonProductPropertyFactoryWithoutListingOwnerTest(DisableWooCommerceSignalsMixin, TestCase, AmazonProductPropertyTestSetupMixin):
    def setUp(self):
        super().setUp()
        self.prepare_test()
        self.sales_channel.listing_owner = False
        self.sales_channel.save()

    def test_not_listing_owner_create_factory_value_only(self):
        fac = AmazonProductPropertyCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product_property,
            remote_product=self.remote_product,
            view=self.view,
            remote_property=self.amazon_property,
            get_value_only=True,
        )

        body = fac.create_body()
        self.assertIsNone(body)
        self.assertEqual(json.loads(fac.remote_value), {})

    def test_not_listing_owner_update_factory_value_only(self):
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
            remote_property=self.amazon_property,
            remote_instance=remote_instance,
            get_value_only=True,
        )
        needs_update = fac.additional_update_check()
        self.assertFalse(needs_update)
        remote_instance.refresh_from_db()
        self.assertEqual(json.loads(remote_instance.remote_value), {})


class AmazonVariationThemeTest(DisableWooCommerceSignalsMixin, TestCase, AmazonProductPropertyTestSetupMixin):
    def setUp(self):
        super().setUp()
        self.prepare_test()

        self.product.type = Product.CONFIGURABLE
        self.product.save()

        # additional size property used for variation matching
        self.size_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="size",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.size_property,
            language=self.multi_tenant_company.language,
            name="Size",
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.size_property,
            code="size",
            type=Property.TYPES.SELECT,
        )
        ProductPropertiesRuleItem.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.size_property,
            defaults={"type": ProductPropertiesRuleItem.OPTIONAL},
        )

        self.remote_rule = AmazonProductType.objects.get(local_instance=self.rule)
        self.remote_rule.variation_themes = ["COLOR/SIZE", "SIZE"]
        self.remote_rule.save()

        self.configurator = RemoteProductConfigurator.objects.create(
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.configurator.properties.set([self.color_property, self.size_property])

    def test_build_variation_attributes_for_child(self):
        child_product = baker.make(
            "products.Product",
            sku="CHILD",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )

        child_remote = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=child_product,
            remote_parent_product=self.remote_product,
            remote_sku="CHILD",
            is_variation=True,
        )

        self.remote_product.remote_sku = "PARENTSKU"
        self.remote_product.save()

        fac = AmazonProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=child_product,
            parent_local_instance=self.product,
            remote_parent_product=self.remote_product,
            remote_instance=child_remote,
            view=self.view,
        )
        fac.remote_rule = self.remote_rule
        AmazonVariationTheme.objects.create(
            product=self.product,
            view=self.view,
            theme="COLOR/SIZE",
            multi_tenant_company=self.multi_tenant_company,
        )
        attrs = fac.build_variation_attributes()

        expected_theme = [{"value": "COLOR/SIZE", "marketplace_id": self.view.remote_id}]
        expected_parentage = [{"value": "child", "marketplace_id": self.view.remote_id}]
        expected_rel = [
            {
                "child_relationship_type": "variation",
                "parent_sku": "PARENTSKU",
                "marketplace_id": self.view.remote_id,
            }
        ]

        self.assertEqual(attrs.get("variation_theme"), expected_theme)
        self.assertEqual(attrs.get("parentage_level"), expected_parentage)
        self.assertEqual(attrs.get("child_parent_sku_relationship"), expected_rel)
