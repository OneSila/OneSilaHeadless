from decimal import Decimal

from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from model_bakery import baker

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import Product, ProductTranslation
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
)
from sales_prices.models import SalesPrice
from sales_channels.integrations.amazon.models import AmazonSalesChannel


CHECK_TEMPLATE_MUTATION = """
    mutation(
        $salesChannel: SalesChannelPartialInput!
        $template: String!
        $language: String!
        $product: ProductPartialInput!
    ) {
      checkSalesChannelContentTemplate(
        salesChannel: $salesChannel
        template: $template
        language: $language
        product: $product
      ) {
        isValid
        renderedContent
        availableVariables
        errors {
          message
          severity
          validationIssue
        }
      }
    }
"""


class CheckSalesChannelContentTemplateMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()

        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )

        ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Sample Product",
            short_description="Short copy",
            description="Long description",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.currency = Currency.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
        ).first()

        if self.currency is None:
            self.currency = Currency.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                iso_code="EUR",
                name="Euro",
                symbol="€",
                is_default_currency=True,
            )

        SalesPrice.objects.create(
            product=self.product,
            currency=self.currency,
            rrp=Decimal("15.00"),
            price=Decimal("12.50"),
            multi_tenant_company=self.multi_tenant_company,
        )

        self.brand_property = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="brand",
        ).first()

        if self.brand_property is None:
            self.brand_property = Property.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Property.TYPES.SELECT,
                is_public_information=True,
                internal_name="brand",
            )

        PropertyTranslation.objects.get_or_create(
            property=self.brand_property,
            language=self.multi_tenant_company.language,
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "name": "Brand",
                "multi_tenant_company": self.multi_tenant_company,
            },
        )

        self.brand_value = PropertySelectValue.objects.create(
            property=self.brand_property,
            multi_tenant_company=self.multi_tenant_company,
        )

        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.brand_value,
            language=self.multi_tenant_company.language,
            value="OneSila",
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductProperty.objects.create(
            product=self.product,
            property=self.brand_property,
            value_select=self.brand_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
            title="Main Image",
        )

        MediaProductThrough.objects.create(
            product=self.product,
            media=self.media,
            sales_channel=self.sales_channel,
            is_main_image=True,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_check_template_mutation_success(self):
        response = self.strawberry_test_client(
            query=CHECK_TEMPLATE_MUTATION,
            variables={
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "template": "<section>{{ title }} - {{ brand }}</section>",
                "language": self.multi_tenant_company.language,
                "product": {"id": self.to_global_id(self.product)},
            },
        )

        self.assertIsNone(response.errors)
        data = response.data["checkSalesChannelContentTemplate"]
        self.assertTrue(data["isValid"])
        self.assertIn("Sample Product", data["renderedContent"])
        self.assertIn("brand", data["availableVariables"])
        self.assertEqual(data["errors"], [])

    def test_check_template_mutation_without_template_preserves_html(self):
        ProductTranslation.objects.filter(
            product=self.product,
            language=self.multi_tenant_company.language,
        ).update(description="<p><strong>Rendered</strong> description</p>")

        response = self.strawberry_test_client(
            query=CHECK_TEMPLATE_MUTATION,
            variables={
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "template": "",
                "language": self.multi_tenant_company.language,
                "product": {"id": self.to_global_id(self.product)},
            },
        )

        self.assertIsNone(response.errors)
        data = response.data["checkSalesChannelContentTemplate"]
        self.assertTrue(data["isValid"])
        self.assertIn("<p><strong>Rendered</strong> description</p>", data["renderedContent"])
        self.assertNotIn("&lt;p&gt;", data["renderedContent"])

    def test_check_template_mutation_returns_errors(self):
        response = self.strawberry_test_client(
            query=CHECK_TEMPLATE_MUTATION,
            variables={
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "template": "{% if title %}",
                "language": self.multi_tenant_company.language,
                "product": {"id": self.to_global_id(self.product)},
            },
        )

        self.assertIsNone(response.errors)
        data = response.data["checkSalesChannelContentTemplate"]
        self.assertFalse(data["isValid"])
        self.assertGreater(len(data["errors"]), 0)
