from core.demo_data import DemoDataLibrary, baker, fake
from faker.providers import BaseProvider
import random

registry = DemoDataLibrary()


@registry.register_private_app
def contacts_company_demo(multi_tenant_company):
    from contacts.models import Company, Person, Address

    for i in range(30):
        fake.seed_instance(i)
        country_code = fake.country_code()
        company = baker.make(Company,
            name=fake.company(),
            multi_tenant_company=multi_tenant_company)
        registry.create_demo_data_relation(company)

        person = baker.make(Person,
                            first_name=fake.first_name(),
                            last_name=fake.last_name(),
                            phone=fake.phone_number(),
                            email=fake.email(),
                            company=company,
                            multi_tenant_company=multi_tenant_company)
        registry.create_demo_data_relation(person)

        address = baker.make(Address,
            company=company,
            vat_number=fake.vat_number(country_code),
            address1=fake.street_address(),
            city=fake.city(),
            postcode=fake.postcode(),
            country=country_code,
            is_shipping_address=True,
            is_invoice_address=True,
            multi_tenant_company=multi_tenant_company,
            person=person)
        registry.create_demo_data_relation(address)