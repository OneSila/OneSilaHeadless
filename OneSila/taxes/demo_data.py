from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from taxes.models import VatRate


registry = DemoDataLibrary()


@registry.register_private_app
def populate_vat_rates(multi_tenant_company):
    if not VatRate.objects.filter(multitenant_company=multi_tenant_company).exists():
        rate = baker.make(VatRate, multi_tenant_company=multi_tenant_company, name='Standard Rate', rate=20)
        registry.create_demo_data_relation(rate)
