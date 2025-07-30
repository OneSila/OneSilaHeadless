from model_bakery import baker
from core.tests import TestCase
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.integrations.amazon.factories import AmazonProductSyncFactory
from sales_channels.integrations.amazon.models.sales_channels import AmazonSalesChannel, AmazonSalesChannelView, AmazonRemoteLanguage
from products.models import Product, ConfigurableVariation
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
    ProductPropertiesRule,
    ProductPropertiesRuleItem,
)

class AmazonConfigurablePropertySelectionTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
            listing_owner=True,
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
            sales_channel_view=self.view,
            remote_code="en",
        )

        # Product type property and rule
        self.product_type_property = Property.objects.filter(is_product_type=True).first()
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
        self.rule, _ = ProductPropertiesRule.objects.get_or_create(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Properties used in tests
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
        self.color_red = baker.make(
            PropertySelectValue,
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.color_blue = baker.make(
            PropertySelectValue,
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.color_red,
            language=self.multi_tenant_company.language,
            value="Red",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.color_blue,
            language=self.multi_tenant_company.language,
            value="Blue",
        )

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
        self.size_m = baker.make(
            PropertySelectValue,
            property=self.size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.size_l = baker.make(
            PropertySelectValue,
            property=self.size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.size_m,
            language=self.multi_tenant_company.language,
            value="M",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.size_l,
            language=self.multi_tenant_company.language,
            value="L",
        )

        self.material_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            internal_name="material",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.material_property,
            language=self.multi_tenant_company.language,
            name="Material",
        )
        self.material_textile = baker.make(
            PropertySelectValue,
            property=self.material_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.material_plastic = baker.make(
            PropertySelectValue,
            property=self.material_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.material_textile,
            language=self.multi_tenant_company.language,
            value="Textile",
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.material_plastic,
            language=self.multi_tenant_company.language,
            value="Plastic",
        )

        self.items_property = baker.make(
            Property,
            type=Property.TYPES.INT,
            internal_name="number_of_items",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.items_property,
            language=self.multi_tenant_company.language,
            name="Number of items",
        )

        # Rule items
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.color_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.size_property,
            type=ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.material_property,
            type=ProductPropertiesRuleItem.REQUIRED,
        )
        ProductPropertiesRuleItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rule=self.rule,
            property=self.items_property,
            type=ProductPropertiesRuleItem.OPTIONAL,
        )

        # Parent product
        self.parent = baker.make(
            "products.Product",
            sku="PARENT",
            type=Product.CONFIGURABLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.parent,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

    def create_variation(self, sku, color, size, material, items):
        variation = baker.make(
            "products.Product",
            sku=sku,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.color_property,
            value_select=color,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.size_property,
            value_select=size,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.material_property,
            value_select=material,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=variation,
            property=self.items_property,
            value_int=items,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.parent,
            variation=variation,
        )
        return variation

    def _run_factory(self):
        fac = AmazonProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.parent,
            view=self.view,
        )
        fac.set_rule()
        fac.set_product_properties()
        return sorted(pp.property.internal_name for pp in fac.product_properties)

    def test_scenario_one_shared_properties(self):
        """
        Scenario 1:
        - Red / M / Textile / 1
        - Blue / M / Textile / 2

        -> configurable properties M Textile
        """
        self.create_variation("V1", self.color_red, self.size_m, self.material_textile, 1)
        self.create_variation("V2", self.color_blue, self.size_m, self.material_textile, 2)
        names = self._run_factory()
        self.assertEqual(sorted(names), ["material", "size"])

    def test_scenario_two_shared_properties(self):
        """
        Scenario 2:
        - Red / M / Textile / 1
        - Blue / L /  Plastic / 1

        -> configurable properties 1
        """
        self.create_variation("V1", self.color_red, self.size_m, self.material_textile, 1)
        self.create_variation("V2", self.color_blue, self.size_l, self.material_plastic, 1)
        names = self._run_factory()
        self.assertEqual(sorted(names), ["number_of_items"])  # only number_of_items shared

    def test_scenario_three_shared_properties(self):
        """
        Scenario 3:
        - Red / M / Textile / 1
        - Red / L /  Textile / 1

        -> configurable properties 1 Textile 1
        """
        self.create_variation("V1", self.color_red, self.size_m, self.material_textile, 1)
        self.create_variation("V2", self.color_red, self.size_l, self.material_textile, 1)
        names = self._run_factory()
        self.assertEqual(sorted(names), ["material", "number_of_items"])
