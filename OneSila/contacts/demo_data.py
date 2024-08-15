from core.demo_data import DemoDataLibrary, baker, fake, PrivateStructuredDataGenerator
from faker.providers import BaseProvider
import random

from contacts.models import Company, Person, Address, InternalShippingAddress, InternalCompany

registry = DemoDataLibrary()


FABRIC_SUPPLIER_NAME = "Midlands Fabric Wholesales ltd"
CUSTOMER_B2B = "Fashion Shop srl"


@registry.register_private_app
class CompanyDataGenerator(PrivateStructuredDataGenerator):
    model = Company

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "name": FABRIC_SUPPLIER_NAME,
                    "email": "mfw@example.com",
                    "language": "GB",
                    "is_supplier": True,
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": CUSTOMER_B2B,
                    "email": "cb2b@example.com",
                    "language": "GB",
                    "is_customer": True,
                },
                'post_data': {},
            }
        ]


@registry.register_private_app
class PersonDataGenerator(PrivateStructuredDataGenerator):
    model = Person

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "company": Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=FABRIC_SUPPLIER_NAME),
                    "first_name": "Jenna",
                    "last_name": "Smith",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=CUSTOMER_B2B),
                    "first_name": "James",
                    "last_name": "Dunn",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            }
        ]


@registry.register_private_app
class AddressDataGenerator(PrivateStructuredDataGenerator):
    model = Address

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "company": Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=FABRIC_SUPPLIER_NAME),
                    "vat_number": fake.vat_number("GB"),
                    "address1": fake.street_address(),
                    "city": fake.city(),
                    "postcode": fake.postcode(),
                    "country": "GB",
                    "is_shipping_address": True,
                    "is_invoice_address": True,
                    "person": Person.objects.get(
                        company=Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=FABRIC_SUPPLIER_NAME)
                    )
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=CUSTOMER_B2B),
                    "vat_number": fake.vat_number("GB"),
                    "address1": fake.street_address(),
                    "city": fake.city(),
                    "postcode": fake.postcode(),
                    "country": "GB",
                    "is_shipping_address": True,
                    "is_invoice_address": True,
                    "person": Person.objects.get(
                        company=Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=CUSTOMER_B2B)
                    ),
                },
                'post_data': {},
            },
        ]


@registry.register_private_app
def optional_internal_address_generation(multi_tenant_company):
    # This code really only applies in tests as frontend generated
    # accounts will have a internal data created through the wizard
    # before demo-data is created.
    try:
        address = InternalShippingAddress.objects.get(multi_tenant_company=multi_tenant_company)
    except InternalShippingAddress.DoesNotExist:
        try:
            internal_company = InternalCompany.objects.get(multi_tenant_company=multi_tenant_company)
        except InternalCompany.DoesNotExist:
            internal_company = InternalCompany.objects.create(
                multi_tenant_company=multi_tenant_company,
                name='Internal Company')
        address = InternalShippingAddress.objects.create(multi_tenant_company=multi_tenant_company,
            company=internal_company,
            address1='Street',
            postcode='Postcode',
            city='City',
            country='GB')

    address.is_invoice_address = True
    address.is_shipping_address = True
    address.save()
    registry.create_demo_data_relation(address)
