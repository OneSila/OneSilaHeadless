from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from core.tests import TestCase
from products.models import SimpleProduct
from sales_prices.models import SalesPriceList, SalesPriceListItem
from currencies.models import Currency
from currencies.currencies import currencies


class SalesPriceConstraintTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.currency, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])

    def test_rrp_only(self):
        rrp = 1000
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        salesprice = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=self.currency,
            rrp=rrp)
        self.assertEqual(salesprice.rrp, rrp)

    def test_price_only(self):
        price = 100
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        salesprice = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=self.currency,
            price=price)
        self.assertEqual(salesprice.price, price)

    def test_no_price(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        with self.assertRaises(IntegrityError):
            salesprice = product.salesprice_set.create(
                multi_tenant_company=self.multi_tenant_company,
                currency=self.currency)
            salesprice.price = 0
            salesprice.rrp = 0
            salesprice.save()

    def test_none_price(self):
        # None prices are needed for backend purposes.
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        salesprice = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=self.currency)
        salesprice.price = None
        salesprice.rrp = None
        salesprice.save()

    def test_none_prices_clean(self):
        # None prices are not desirable from the frontend.
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        with self.assertRaises(ValidationError):
            salesprice = product.salesprice_set.create(
                multi_tenant_company=self.multi_tenant_company,
                currency=self.currency)
            salesprice.price = None
            salesprice.rrp = None
            salesprice.clean()

    def test_both_prices(self):
        rrp = 100
        price = 90
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        salesprice = product.salesprice_set.create(
            multi_tenant_company=self.multi_tenant_company,
            currency=self.currency,
            rrp=rrp,
            price=price)
        self.assertEqual(salesprice.rrp, rrp)
        self.assertEqual(salesprice.price, price)

    def test_rrp_gt_price(self):
        rrp = 90
        price = 100
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        with self.assertRaises(IntegrityError):
            salesprice = product.salesprice_set.create(
                multi_tenant_company=self.multi_tenant_company,
                currency=self.currency,
                rrp=rrp,
                price=price)


class SalesPriceListItemQuerySetTestCase(TestCase):
    def test_annotate_prices(self):
        # We want to ensure that the prices are returned correctly
        # especially when price list settings are changes.
        rrp = 1000
        price = 900

        price_auto = 800
        price_override = 700

        discount_auto = 600
        discount_override = None

        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        currency, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])
        salesprice, _ = product.salesprice_set.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            currency=currency)
        salesprice.set_prices(rrp=rrp, price=price)

        price_list = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name='Test list test_discount_price',
            auto_update_prices=True,
            currency=currency,
        )

        price_list_price = SalesPriceListItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            salespricelist=price_list,
            product=product,
            price_auto=price_auto,
            price_override=price_override,
            discount_auto=discount_auto,
            discount_override=discount_override,
        )
        price_list_price = SalesPriceListItem.objects.get(id=price_list_price.id)

        # When the price list is auto-updating, we expect overrides to be more
        # important then auto fields. But if there is no override, we expect an auto-field.
        self.assertTrue(price_list.auto_update_prices)
        self.assertEqual(price_list_price.price, price_list_price.price_override)
        self.assertEqual(price_list_price.discount, price_list_price.discount_auto)

        price_list.auto_update_prices = False
        price_list.save()

        # FIXME: You seem to have to reload the object to get the right results below.
        # Unclear whether this is Django cache related or dirty-field related.
        # Related to? https://code.djangoproject.com/ticket/29263#no1
        price_list_price = SalesPriceListItem.objects.get(id=price_list_price.id)

        # When the price list is not auto-updating you expect to receive only the override
        # field.
        self.assertFalse(price_list.auto_update_prices)
        self.assertFalse(price_list_price.salespricelist.auto_update_prices)
        self.assertEqual(price_list_price.price, price_list_price.price_override)
        self.assertEqual(price_list_price.discount, price_list_price.discount_override)
