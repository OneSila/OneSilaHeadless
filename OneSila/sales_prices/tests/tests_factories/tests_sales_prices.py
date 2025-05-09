from sales_prices.factories import SalesPriceUpdateCreateFactory
from sales_prices.flows import salesprice_create_for_currency_flow
from core.tests import TestCase

from products.models import SimpleProduct
from currencies.models import Currency
from sales_prices.models import SalesPrice

from currencies.helpers import currency_convert
from currencies.currencies import currencies

import logging
logger = logging.getLogger(__name__)


class SalesPriceCreateForCurrencyFactoryTestCase(TestCase):
    def test_new_currency_created_for_company(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company, active=True)
        currency_default, _ = Currency.objects.get_or_create(is_default_currency=True, multi_tenant_company=self.multi_tenant_company, **currencies['GB'])
        salesprice_create_for_currency_flow(currency_default)

        self.assertFalse(product.salesprice_set.filter(currency=currency_default).exists())

        currency_non_default, _ = Currency.objects.get_or_create(is_default_currency=False, multi_tenant_company=self.multi_tenant_company, **currencies['BE'])
        salesprice_create_for_currency_flow(currency_non_default)

        self.assertTrue(product.salesprice_set.filter(currency=currency_non_default).exists())


class SalesPriceUpdateCreateFactoryTestCase(TestCase):
    def test_salesprice_with_discount(self):
        """
        The tasks should create and update all the other prices.
        """
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company, active=True)
        currency, _ = Currency.objects.get_or_create(is_default_currency=True, multi_tenant_company=self.multi_tenant_company, **currencies['GB'])
        other_currency, _ = Currency.objects.get_or_create(
            is_default_currency=False,
            multi_tenant_company=self.multi_tenant_company,
            inherits_from=currency,
            follow_official_rate=False,
            exchange_rate=1.3,
            **currencies['BE'])

        ori_main_price_instance, _ = SalesPrice.objects.get_or_create(
            product=product,
            currency=currency,
            multi_tenant_company=self.multi_tenant_company)
        ori_main_price_instance.set_prices(rrp=100, price=90)
        ori_main_price_instance.refresh_from_db()

        f = SalesPriceUpdateCreateFactory(ori_main_price_instance)
        f.run()

        ori_other_price_instance = SalesPrice.objects.get(product=product, currency=other_currency)

        ori_main_price = ori_main_price_instance.rrp
        ori_main_price_discount = ori_main_price_instance.price

        ori_other_price = ori_other_price_instance.rrp
        ori_other_price_discount = ori_other_price_instance.price

        self.assertTrue(ori_main_price != ori_other_price)
        self.assertTrue(ori_other_price is not None)
        self.assertTrue(ori_main_price_discount != ori_other_price_discount)
        self.assertTrue(ori_other_price_discount is not None)

        ori_main_price_instance.rrp = ori_main_price_instance.rrp * 2
        ori_main_price_instance.price = float(ori_main_price_instance.price) * 1.5
        ori_main_price_instance.save()

        f = SalesPriceUpdateCreateFactory(ori_main_price_instance)
        f.run()

        changed_main_price = ori_main_price_instance.rrp
        changed_main_price_discount = ori_main_price_instance.price

        ori_other_price_instance.refresh_from_db()

        changed_other_price = ori_other_price_instance.rrp
        changed_other_price_discount = ori_other_price_instance.price

        self.assertFalse(ori_other_price == changed_other_price)
        self.assertFalse(ori_other_price_discount == changed_other_price_discount)

    def test_salesprice_without_discount(self):
        """
        The tasks should create and update all the other prices.
        """
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company, active=True)
        currency, _ = Currency.objects.get_or_create(is_default_currency=True, multi_tenant_company=self.multi_tenant_company, **currencies['GB'])
        other_currency, _ = Currency.objects.get_or_create(
            is_default_currency=False,
            multi_tenant_company=self.multi_tenant_company,
            inherits_from=currency,
            follow_official_rate=False,
            exchange_rate=1.3,
            **currencies['BE'])

        ori_main_price_instance, _ = SalesPrice.objects.get_or_create(
            product=product,
            currency=currency,
            multi_tenant_company=self.multi_tenant_company)
        ori_main_price_instance.set_prices(rrp=100, price=None)
        ori_main_price_instance.refresh_from_db()

        f = SalesPriceUpdateCreateFactory(ori_main_price_instance)
        f.run()

        ori_other_price_instance = SalesPrice.objects.get(product=product, currency=other_currency)

        ori_main_price = ori_main_price_instance.rrp
        ori_main_price_discount = ori_main_price_instance.price

        ori_other_price = ori_other_price_instance.rrp
        ori_other_price_discount = ori_other_price_instance.price

        self.assertTrue(ori_main_price != ori_other_price)
        self.assertTrue(ori_other_price is not None)
        self.assertTrue(ori_main_price_discount == ori_other_price_discount)
        self.assertTrue(ori_other_price_discount is None)

        ori_main_price_instance.rrp = ori_main_price_instance.rrp * 2
        ori_main_price_instance.save()

        f = SalesPriceUpdateCreateFactory(ori_main_price_instance)
        f.run()

        changed_main_price = ori_main_price_instance.rrp
        changed_main_price_discount = ori_main_price_instance.price

        ori_other_price_instance.refresh_from_db()

        changed_other_price = ori_other_price_instance.rrp
        changed_other_price_discount = ori_other_price_instance.price

        self.assertFalse(ori_other_price == changed_other_price)
        self.assertTrue(ori_other_price is not None)
        self.assertTrue(ori_other_price_discount == changed_other_price_discount)
        self.assertTrue(ori_other_price_discount is None)
