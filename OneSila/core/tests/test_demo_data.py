from core.tests import TestCase, baker
from core.demo_data import DemoDataLibrary
from django.contrib.auth import get_user_model


class DemoDataTestCase(TestCase):
    def test_populate_demo_data(self):
        # You should be able to create test-data, remove it - and add it again.
        # failure to do so means that there are one or more generators that are
        # not registering relations and triggering unique integrity errors
        # we will do this for two different mtcs
        registry = DemoDataLibrary()

        mtc = baker.make('core.multiTenantCompany')
        user = baker.make(get_user_model(), multi_tenant_company=mtc,
            is_multi_tenant_company_owner=True)

        registry.run(multi_tenant_company=mtc)
        registry.delete_demo_data(multi_tenant_company=mtc)

        mtc_bis = baker.make('core.multiTenantCompany')
        user = baker.make(get_user_model(), multi_tenant_company=mtc_bis,
            is_multi_tenant_company_owner=True)

        registry.run(multi_tenant_company=mtc_bis)
        registry.delete_demo_data(multi_tenant_company=mtc_bis)
