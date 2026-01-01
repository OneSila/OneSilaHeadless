from core.tests import TestCase
from llm.factories.bulk_content_context import BulkContentContextBuilder
from products.models import ConfigurableProduct, ConfigurableVariation, SimpleProduct
from properties.models import (
    ProductProperty,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
    PropertyTranslation,
)


class BulkContentContextBuilderTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.multi_tenant_company.language = "en"
        self.multi_tenant_company.save()

        self.parent = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="CONFIG-1",
        )
        self.variation_red = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SIMPLE-RED",
        )
        self.variation_blue = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="SIMPLE-BLUE",
        )
        ConfigurableVariation.objects.create(
            parent=self.parent,
            variation=self.variation_red,
        )
        ConfigurableVariation.objects.create(
            parent=self.parent,
            variation=self.variation_blue,
        )

        self.color_property = Property.objects.create(
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertyTranslation.objects.create(
            property=self.color_property,
            name="Color",
            language="en",
            multi_tenant_company=self.multi_tenant_company,
        )
        red_value = PropertySelectValue.objects.create(
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        blue_value = PropertySelectValue.objects.create(
            property=self.color_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=red_value,
            value="Red",
            language="en",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=blue_value,
            value="Blue",
            language="en",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.variation_red,
            property=self.color_property,
            value_select=red_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.variation_blue,
            property=self.color_property,
            value_select=blue_value,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_configurable_common_properties_not_repeated_in_variations(self):
        builder = BulkContentContextBuilder(
            multi_tenant_company=self.multi_tenant_company,
            products=[self.parent],
            default_language="en",
        )
        builder.build()

        context = builder.build_product_context(
            product=self.parent,
            languages=["en"],
            default_language="en",
        )

        properties = context["properties"]
        self.assertEqual(properties["common"]["Color"], ["Blue", "Red"])
        variation_skus = {entry["sku"] for entry in properties["variations"]}
        self.assertEqual(variation_skus, {self.variation_red.sku, self.variation_blue.sku})
        for entry in properties["variations"]:
            self.assertNotIn("properties", entry)

    def test_configurable_variations_limited_to_max(self):
        for index in range(11):
            variation = SimpleProduct.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sku=f"VAR-{index:02d}",
            )
            ConfigurableVariation.objects.create(
                parent=self.parent,
                variation=variation,
            )

        builder = BulkContentContextBuilder(
            multi_tenant_company=self.multi_tenant_company,
            products=[self.parent],
            default_language="en",
        )
        builder.build()

        context = builder.build_product_context(
            product=self.parent,
            languages=["en"],
            default_language="en",
        )

        variation_skus = [entry["sku"] for entry in context["properties"]["variations"]]
        self.assertEqual(len(variation_skus), builder.MAX_VARIATIONS_CONTEXT)
        self.assertEqual(variation_skus, sorted(variation_skus))
