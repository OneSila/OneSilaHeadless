from datetime import date

from core.tests import TestCase
from imports_exports.factories.sales_prices import ImportSalesPriceListInstance
from imports_exports.models import Import
from sales_prices.models import SalesPriceList


class ImportSalesPriceListInstanceTests(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_create_without_dates(self):
        data = {
            'name': 'Retail',
        }
        inst = ImportSalesPriceListInstance(
            data, self.import_process, currency_object=self.currency
        )
        inst.process()
        self.assertIsNotNone(inst.instance)
        self.assertIsNone(inst.instance.start_date)
        self.assertIsNone(inst.instance.end_date)
        self.assertEqual(inst.instance.name, 'Retail')

    def test_create_with_dates(self):
        data = {
            'name': 'Promo',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 12, 31),
        }
        inst = ImportSalesPriceListInstance(
            data, self.import_process, currency_object=self.currency
        )
        inst.process()
        self.assertEqual(inst.instance.start_date, date(2024, 1, 1))
        self.assertEqual(inst.instance.end_date, date(2024, 12, 31))

    def test_get_or_create_updates_existing(self):
        existing = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name='Retail',
            currency=self.currency,
            vat_included=False,
            auto_update_prices=True,
        )
        data = {
            'name': 'Retail',
            'vat_included': True,
            'auto_update_prices': False,
        }
        inst = ImportSalesPriceListInstance(
            data, self.import_process, currency_object=self.currency
        )
        inst.process()
        self.assertEqual(inst.instance.id, existing.id)
        self.assertTrue(inst.instance.vat_included)
        self.assertFalse(inst.instance.auto_update_prices)

    def test_given_instance_updates_fields(self):
        existing = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name='Wholesale',
            currency=self.currency,
            vat_included=False,
            auto_update_prices=True,
        )
        data = {
            'vat_included': True,
            'auto_update_prices': False,
        }
        inst = ImportSalesPriceListInstance(
            data, self.import_process, currency_object=self.currency, instance=existing
        )
        inst.process()
        self.assertEqual(inst.instance.id, existing.id)
        self.assertTrue(inst.instance.vat_included)
        self.assertFalse(inst.instance.auto_update_prices)
