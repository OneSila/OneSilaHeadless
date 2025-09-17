from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.models import SalesChannel, SalesChannelIntegrationPricelist, RemoteProduct
from sales_channels.receivers import sales_channels__sales_channel__post_create_receiver
from core.signals import post_create
from unittest.mock import patch
from sales_prices.models import SalesPriceList
from currencies.models import Currency
from currencies.currencies import currencies


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