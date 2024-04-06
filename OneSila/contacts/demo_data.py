from core.demo_data import DemoData
from model_bakery import baker


registry = DemoData()


def app_demo_data(multi_tenant_user):
    from contacts.models import Company

    baker.make(Company, _quantity=3)


registry.register(app_demo_data)
