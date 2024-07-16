from core.demo_data import DemoDataLibrary, baker, fake
from faker.providers import BaseProvider
import random

registry = DemoDataLibrary()


def generate_company_types(is_first=False):
    if is_first:
        # If it's the first company, make it an internal company
        return {
            'is_supplier': False,
            'is_customer': False,
            'is_influencer': False,
            'is_internal_company': True
        }
    else:
        return {
            'is_supplier': random.choice([True, False]),
            'is_customer': random.choice([True, False]),
            'is_influencer': random.choice([True, False]),
            'is_internal_company': False
        }


@registry.register_private_app
def contacts_company_demo(multi_tenant_company):
    from contacts.models import Company, Person, Address

    for i in range(50):
        fake.seed_instance(i)
        country_code = fake.country_code()
        types = generate_company_types(is_first=(i == 0))
        company = baker.make(Company,
            name=fake.company(),
            email=fake.email(),
            language=random.choice(['EN', 'FR', 'RU', 'DE', 'NL', 'NL']),
            multi_tenant_company=multi_tenant_company, **types)
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
