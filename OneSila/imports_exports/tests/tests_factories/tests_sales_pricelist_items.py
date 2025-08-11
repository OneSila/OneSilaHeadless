from core.tests import TestCase
from imports_exports.models import Import
from imports_exports.factories.sales_prices import (
    ImportSalesPriceListItemInstance,
    ImportSalesPriceListInstance,
)
from imports_exports.factories.products import ImportProductInstance
from products.models import SimpleProduct
from sales_prices.models import SalesPriceList, SalesPrice


class ImportSalesPriceListItemInstanceTests(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def _create_product_with_sales_price(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        sales_price, _ = product.salesprice_set.get_or_create(
            multi_tenant_company=self.multi_tenant_company, currency=self.currency
        )
        sales_price.set_prices(rrp=100, price=90)
        return product

    def _create_pricelist(self):
        return SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Retail",
            currency=self.currency,
        )

    def test_create_with_objects(self):
        product = self._create_product_with_sales_price()
        pricelist = self._create_pricelist()
        inst = ImportSalesPriceListItemInstance(
            {}, self.import_process, sales_pricelist=pricelist, product=product
        )
        inst.process()
        item = inst.instance
        self.assertTrue(pricelist.salespricelistitem_set.filter(product=product).exists())
        self.assertIsNotNone(item.price_auto)
        self.assertIsNotNone(item.discount_auto)

    def test_create_with_product_data(self):
        pricelist = self._create_pricelist()
        data = {"product_data": {"name": "Widget", "properties": []}, "disable_auto_update": True}
        inst = ImportSalesPriceListItemInstance(
            data, self.import_process, sales_pricelist=pricelist
        )
        inst.process()
        item = inst.instance
        self.assertEqual(item.product.name, "Widget")

    def test_disable_auto_update(self):
        product = self._create_product_with_sales_price()
        pricelist = self._create_pricelist()
        inst = ImportSalesPriceListItemInstance(
            {},
            self.import_process,
            sales_pricelist=pricelist,
            product=product,
            disable_auto_update=True,
        )
        inst.process()
        item = inst.instance
        self.assertIsNone(item.price_auto)
        self.assertIsNone(item.discount_auto)


class ImportSalesPriceListWithItemsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_sales_pricelist_with_items(self):
        product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        sales_price, _ = product.salesprice_set.get_or_create(
            multi_tenant_company=self.multi_tenant_company, currency=self.currency
        )
        sales_price.set_prices(rrp=100, price=90)
        data = {
            "name": "Promo",
            "sales_pricelist_items": [{"product": product}],
        }
        inst = ImportSalesPriceListInstance(
            data, self.import_process, currency=self.currency
        )
        inst.process()
        self.assertTrue(inst.instance.salespricelistitem_set.filter(product=product).exists())

    def test_product_with_sales_pricelist_items(self):
        pricelist = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Retail",
            currency=self.currency,
        )
        product_data = {
            "name": "Imported",
            "properties": [],
            "sales_pricelist_items": [
                {"salespricelist": pricelist, "disable_auto_update": True}
            ],
        }
        inst = ImportProductInstance(product_data, self.import_process)
        inst.process()
        product = inst.instance
        self.assertTrue(pricelist.salespricelistitem_set.filter(product=product).exists())
