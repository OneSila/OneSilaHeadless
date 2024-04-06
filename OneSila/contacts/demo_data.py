from core.demo_data import DemoDataLibrary, baker, faker


registry = DemoDataLibrary()


@registry.register_private_app
def contacts_company_demo(multi_tenant_user):
    from contacts.models import Company

    for i in range(3):
        baker.make(Company, name=faker.company())
