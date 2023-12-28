from contacts.models import Company, Supplier
from django.test import TestCase
from core.tests import TestCaseMixin


class CompanyTestCase(TestCaseMixin, TestCase):
    def test_supplier_create(self):
        supplier = Supplier.objects.create(name='test_supplier_create', multi_tenant_company=self.multi_tenant_company)
        self.assertTrue(supplier.is_supplier)

    def test_supplier_qstype(self):
        supplier_id = Supplier.objects.create(name='test_supplier_create', multi_tenant_company=self.multi_tenant_company).id
        supplier = Supplier.objects.get(id=supplier_id)
        all_suppliers = Supplier.objects.all()

        self.assertTrue(all_suppliers, Supplier.objects)
        self.assertTrue(supplier, Supplier)

    def test_supplier_search(self):
        supplier_id = Supplier.objects.create(name='test_search_supplier', multi_tenant_company=self.multi_tenant_company).id
        supplier = Supplier.objects.get(id=supplier_id)

        qs = Supplier.objects.search('supplier')

        self.assertTrue(qs.exists())
