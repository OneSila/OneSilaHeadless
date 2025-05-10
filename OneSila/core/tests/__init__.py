from core.models import MultiTenantCompany
from django.contrib.auth import get_user_model
from model_bakery import baker
from django.test import TestCase as DjangoTestCase
from django.test import TransactionTestCase as DjangoTransactionTestCase
from .tests_schemas.tests_queries import TransactionTestCaseMixin
from currencies.models import Currency
from core.demo_data import DemoDataLibrary
from currencies.currencies import currencies


class TestCaseMixin:
    def setUp(self):
        super().setUp()
        self.multi_tenant_company = baker.make(MultiTenantCompany)
        self.currency, _ = Currency.objects.get_or_create(
            is_default_currency=True,
            multi_tenant_company=self.multi_tenant_company,
            **currencies['GB'])

        self.user = baker.make(get_user_model(), multi_tenant_company=self.multi_tenant_company)
        self.user.is_multi_tenant_company_owner = True
        self.user.save()


class TestCase(TestCaseMixin, DjangoTestCase):
    pass


class TransactionTestCase(TestCaseMixin, DjangoTransactionTestCase):
    pass


class TestCaseDemoDataMixin:
    # This variable will be shared across all TestCases subsclassed from here.
    # That will ensure we only try to generate the demo-data once.
    demo_data_generated = False

    def generate_demo_data(self):
        if not self.demo_data_generated:
            self.demo_data_registry = DemoDataLibrary()
            self.demo_data_registry.run(multi_tenant_company=self.multi_tenant_company)
            self.demo_data_generated = True

    def setUp(self):
        super().setUp()
        self.generate_demo_data()

    def tearDown(self):
        self.demo_data_registry.delete_demo_data(multi_tenant_company=self.multi_tenant_company)
        self.demo_data_generated = False


class TestCaseWithDemoData(TestCaseDemoDataMixin, TestCase):
    pass
