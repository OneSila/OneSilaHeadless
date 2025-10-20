from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import RequestFactory
from django.utils.html import format_html
from core.tests import TestCase
from model_bakery import baker

from products.models import Product, ProductTranslation
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import SalesChannel, SalesChannelIntegrationPricelist, RemoteProduct, SalesChannelContentTemplate
from sales_channels.views import sales_channel_content_template_preview
from sales_channels.receivers import sales_channels__sales_channel__post_create_receiver
from core.signals import post_create
from unittest.mock import patch
from sales_prices.models import SalesPriceList, SalesPrice
from currencies.models import Currency
from currencies.currencies import currencies
from media.models import Media, MediaProductThrough
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation, ProductProperty
from sales_channels.content_templates import build_content_template_context, render_sales_channel_content_template


class SalesChannelIntegrationPricelistTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.eur, _ = Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company, **currencies["DE"]
        )
        self.usd, _ = Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company, **currencies["US"]
        )

    def _create_pricelist(self, name, currency, start=None, end=None):
        return SalesPriceList.objects.create(
            name=name,
            currency=currency,
            start_date=start,
            end_date=end,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_different_currency_overlapping_allowed(self):
        pl1 = self._create_pricelist(
            "pl1", self.eur, date(2025, 8, 1), date(2025, 9, 1)
        )
        pl2 = self._create_pricelist(
            "pl2", self.usd, date(2025, 8, 1), date(2025, 9, 1)
        )

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl1,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl2,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_overlapping_same_currency_not_allowed(self):
        pl1 = self._create_pricelist(
            "pl1", self.eur, date(2025, 8, 1), date(2025, 9, 1)
        )
        pl2 = self._create_pricelist(
            "pl2", self.eur, date(2025, 8, 24), date(2025, 9, 24)
        )

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl1,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(ValidationError):
            SalesChannelIntegrationPricelist.objects.create(
                sales_channel=self.channel,
                price_list=pl2,
                multi_tenant_company=self.multi_tenant_company,
            )

    def test_open_ended_pricelist_not_allowed(self):
        with self.assertRaises(ValidationError):
            self._create_pricelist("pl1", self.eur, date(2025, 8, 1), None)

        with self.assertRaises(ValidationError):
            self._create_pricelist("pl2", self.eur, None, date(2026, 1, 1))

    def test_multiple_base_pricelists_not_allowed(self):
        pl1 = self._create_pricelist("pl1", self.eur)
        pl2 = self._create_pricelist("pl2", self.eur)

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl1,
            multi_tenant_company=self.multi_tenant_company,
        )

        with self.assertRaises(ValidationError):
            SalesChannelIntegrationPricelist.objects.create(
                sales_channel=self.channel,
                price_list=pl2,
                multi_tenant_company=self.multi_tenant_company,
            )

    def test_non_overlapping_same_currency_allowed(self):
        pl1 = self._create_pricelist(
            "pl1", self.eur, date(2025, 8, 1), date(2025, 9, 1)
        )
        pl2 = self._create_pricelist(
            "pl2", self.eur, date(2025, 9, 2), date(2025, 10, 1)
        )

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl1,
            multi_tenant_company=self.multi_tenant_company,
        )

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl2,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_non_overlapping_same_currency_default_and_with_dates(self):
        pl1 = self._create_pricelist(
            "pl1", self.eur, date(2025, 8, 1), date(2025, 9, 1)
        )
        pl2 = self._create_pricelist(
            "pl2", self.eur
        )

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl1,
            multi_tenant_company=self.multi_tenant_company,
        )

        SalesChannelIntegrationPricelist.objects.create(
            sales_channel=self.channel,
            price_list=pl2,
            multi_tenant_company=self.multi_tenant_company,
        )



class RemoteProductConstraintTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://channel.example.com",
        )
        self.parent_product_a = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE
        )
        self.parent_product_b = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE
        )
        self.child_product_a = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE
        )
        self.child_product_b = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE
        )

        self.parent_remote_a = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.parent_product_a,
            remote_sku="PARENT-A",
            is_variation=False,
        )
        self.parent_remote_b = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.parent_product_b,
            remote_sku="PARENT-B",
            is_variation=False,
        )

    def test_variation_sku_can_repeat_for_different_parents(self):
        RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.child_product_a,
            remote_parent_product=self.parent_remote_a,
            remote_sku="SHARED-SKU",
            is_variation=True,
        )

        duplicate_with_other_parent = RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.child_product_b,
            remote_parent_product=self.parent_remote_b,
            remote_sku="SHARED-SKU",
            is_variation=True,
        )

        self.assertIsNotNone(duplicate_with_other_parent.pk)

    def test_variation_sku_cannot_repeat_for_same_parent(self):
        RemoteProduct.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=self.child_product_a,
            remote_parent_product=self.parent_remote_a,
            remote_sku="DUP-SKU",
            is_variation=True,
        )

        with self.assertRaises(IntegrityError):
            RemoteProduct.objects.create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
                local_instance=self.child_product_b,
                remote_parent_product=self.parent_remote_a,
                remote_sku="DUP-SKU",
                is_variation=True,
            )


class SalesChannelContentTemplateTestCase(TestCase):
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

        self.request_factory = RequestFactory()

    def test_build_content_template_context(self):
        context = build_content_template_context(
            product=self.product,
            sales_channel=self.sales_channel,
            description="Rendered description",
            language=self.multi_tenant_company.language,
            title="Sample Product",
        )

        self.assertEqual(context["content"], "Rendered description")
        self.assertEqual(context["title"], "Sample Product")
        self.assertEqual(context["brand"], "OneSila")
        self.assertEqual(context["currency"], self.currency.iso_code)
        self.assertEqual(context["price"], Decimal("15.00"))
        self.assertIn("product_properties", context)
        self.assertTrue(
            any(prop["internal_name"] == "brand" for prop in context["product_properties"])
        )

    def test_build_content_template_context_with_price_overrides(self):
        context = build_content_template_context(
            product=self.product,
            sales_channel=self.sales_channel,
            description="Rendered description",
            language=self.multi_tenant_company.language,
            title="Sample Product",
            price=Decimal("99.99"),
            discount_price=Decimal("79.99"),
            currency="USD",
        )

        self.assertEqual(context["price"], Decimal("99.99"))
        self.assertEqual(context["discount_price"], Decimal("79.99"))
        self.assertEqual(context["currency"], "USD")

    def test_render_sales_channel_content_template(self):
        context = build_content_template_context(
            product=self.product,
            sales_channel=self.sales_channel,
            description="Rendered description",
            language=self.multi_tenant_company.language,
            title="Sample Product",
        )

        template = "<div>{{ title }} - {{ brand }}</div>"
        rendered = render_sales_channel_content_template(
            template_string=template,
            context=context,
        )

        self.assertIn("Sample Product", rendered)
        self.assertIn("OneSila", rendered)

    def test_render_sales_channel_content_template_preserves_html(self):
        context = build_content_template_context(
            product=self.product,
            sales_channel=self.sales_channel,
            description="<b>Rendered</b> & description",
            language=self.multi_tenant_company.language,
            title="Sample Product",
        )

        template = "<div>{{ content }}</div>"
        rendered = render_sales_channel_content_template(
            template_string=template,
            context=context,
        )

        self.assertIn("<b>Rendered</b> & description", rendered)
        self.assertNotIn("&lt;b&gt;Rendered&lt;/b&gt;", rendered)

    def test_render_sales_channel_content_template_as_iframe(self):
        iframe_src = "https://example.com/template/1/product/2/"
        rendered = render_sales_channel_content_template(
            template_string="<div>ignored</div>",
            context={
                "iframe": format_html(
                    '<iframe id="desc_ifr" title="Seller\'s description of item" '
                    "sandbox=\"allow-scripts allow-popups allow-popups-to-escape-sandbox allow-same-origin\" "
                    "height=\"2950px\" width=\"100%\" marginheight=\"0\" marginwidth=\"0\" frameborder=\"0\" "
                    'src="{}" loading="lazy"></iframe>',
                    iframe_src,
                )
            },
        )

        self.assertIn("<iframe", rendered)
        self.assertIn(iframe_src, rendered)

    def test_template_preview_view_returns_rendered_content(self):
        template = SalesChannelContentTemplate(
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
            template="<div>{{ title }}</div>",
            multi_tenant_company=self.multi_tenant_company,
        )
        template.id = 999

        request = self.request_factory.get("/")
        with patch(
            "sales_channels.views.get_object_or_404",
            side_effect=[template, self.product],
        ):
            response = sales_channel_content_template_preview(
                request,
                template_id=template.id,
                product_id=self.product.id,
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Sample Product", response.content.decode())

    def test_template_preview_view_renders_html_description(self):
        ProductTranslation.objects.filter(
            product=self.product,
            language=self.multi_tenant_company.language,
        ).update(description="<p><strong>Rendered</strong> description</p>")

        template = SalesChannelContentTemplate(
            sales_channel=self.sales_channel,
            language=self.multi_tenant_company.language,
            template="<div>{{ content }}</div>",
            multi_tenant_company=self.multi_tenant_company,
        )
        template.id = 1001

        request = self.request_factory.get("/")
        with patch(
            "sales_channels.views.get_object_or_404",
            side_effect=[template, self.product],
        ):
            response = sales_channel_content_template_preview(
                request,
                template_id=template.id,
                product_id=self.product.id,
            )

        html = response.content.decode()
        self.assertIn("<p><strong>Rendered</strong> description</p>", html)
        self.assertNotIn("&lt;p&gt;", html)
