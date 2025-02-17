from core.demo_data import DemoDataLibrary, baker, fake, PrivateStructuredDataGenerator
from faker.providers import BaseProvider
import random

from contacts.models import Company, Person, Address, InternalShippingAddress, InternalCompany

registry = DemoDataLibrary()


CUSTOMER_B2B = "Luxury Home Interiors Ltd"

INTERNAL_SHIPPING_STREET_ONE = "The Strand 23"
INTERNAL_SHIPPING_STREET_TWO = "Jameson Street 201"

WOOD_SUPPLIER_ONE_NAME = "Timber & Co."
WOOD_SUPPLIER_TWO_NAME = "Hardwood Masters"
METAL_SUPPLIER_NAME = "SteelWorks Ltd."
GLASS_SUPPLIER_NAME = "CrystalClear Glass"
BED_SUPPLIER_NAME = "Dreamy Comfort Bedding"


class CompanyGetDataMixin:
    def get_company(self, name):
        return Company.objects.get(multi_tenant_company=self.multi_tenant_company, name=name)

    def get_person(self, company_name):
        return Person.objects.filter(company=self.get_company(company_name)).order_by("?").last()


@registry.register_private_app
class CompanyDataGenerator(PrivateStructuredDataGenerator):
    model = Company

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "name": GLASS_SUPPLIER_NAME,
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
            },
            {
                'instance_data': {
                    "name": WOOD_SUPPLIER_ONE_NAME,
                    "email": fake.email(),
                    "language": "GB",
                    "is_supplier": True,
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": WOOD_SUPPLIER_TWO_NAME,
                    "email": fake.email(),
                    "language": "GB",
                    "is_supplier": True,
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": METAL_SUPPLIER_NAME,
                    "email": fake.email(),
                    "language": "GB",
                    "is_supplier": True,
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": BED_SUPPLIER_NAME,
                    "email": fake.email(),
                    "language": "GB",
                    "is_supplier": True,
                },
                'post_data': {},
            },
        ]


@registry.register_private_app
class PersonDataGenerator(CompanyGetDataMixin, PrivateStructuredDataGenerator):
    model = Person

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "company": self.get_company(GLASS_SUPPLIER_NAME),
                    "first_name": "Jenna",
                    "last_name": "Smith",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(CUSTOMER_B2B),
                    "first_name": "James",
                    "last_name": "Dunn",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(WOOD_SUPPLIER_ONE_NAME),
                    "first_name": "Tom",
                    "last_name": "Dickens",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(WOOD_SUPPLIER_TWO_NAME),
                    "first_name": "Jamie",
                    "last_name": "James",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(WOOD_SUPPLIER_TWO_NAME),
                    "first_name": "Jane",
                    "last_name": "James",
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                },
                'post_data': {},
            },
        ]


@registry.register_private_app
class AddressDataGenerator(CompanyGetDataMixin, PrivateStructuredDataGenerator):
    model = Address

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "company": self.get_company(GLASS_SUPPLIER_NAME),
                    "vat_number": fake.vat_number("GB"),
                    "address1": fake.street_address(),
                    "city": fake.city(),
                    "postcode": fake.postcode(),
                    "country": "GB",
                    "is_shipping_address": True,
                    "is_invoice_address": True,
                    "person": self.get_person(GLASS_SUPPLIER_NAME),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(CUSTOMER_B2B),
                    "vat_number": fake.vat_number("GB"),
                    "address1": fake.street_address(),
                    "city": fake.city(),
                    "postcode": fake.postcode(),
                    "country": "GB",
                    "is_shipping_address": True,
                    "is_invoice_address": True,
                    "person": self.get_person(CUSTOMER_B2B),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(WOOD_SUPPLIER_ONE_NAME),
                    "vat_number": fake.vat_number("GB"),
                    "address1": fake.street_address(),
                    "city": fake.city(),
                    "postcode": fake.postcode(),
                    "country": "GB",
                    "is_shipping_address": True,
                    "is_invoice_address": True,
                    "person": self.get_person(WOOD_SUPPLIER_ONE_NAME),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "company": self.get_company(WOOD_SUPPLIER_TWO_NAME),
                    "vat_number": fake.vat_number("GB"),
                    "address1": fake.street_address(),
                    "city": fake.city(),
                    "postcode": fake.postcode(),
                    "country": "GB",
                    "is_shipping_address": True,
                    "is_invoice_address": True,
                    "person": self.get_person(WOOD_SUPPLIER_TWO_NAME),
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
        address_one = InternalShippingAddress.objects.get(multi_tenant_company=multi_tenant_company)
    except InternalShippingAddress.DoesNotExist:
        try:
            internal_company = InternalCompany.objects.get(multi_tenant_company=multi_tenant_company)
        except InternalCompany.DoesNotExist:
            internal_company = InternalCompany.objects.create(
                multi_tenant_company=multi_tenant_company,
                name='Internal Company')

        address_one = InternalShippingAddress.objects.create(multi_tenant_company=multi_tenant_company,
            company=internal_company,
            address1=INTERNAL_SHIPPING_STREET_ONE,
            postcode='LN12 23AF',
            city='London',
            country='GB')

        # We stuff this in here, as this case most likely means that it's demo-data.
        address_two = InternalShippingAddress.objects.create(multi_tenant_company=multi_tenant_company,
            company=internal_company,
            address1=INTERNAL_SHIPPING_STREET_TWO,
            postcode='BM2 3TS',
            city='Birmingham',
            country='GB')

        address_two.is_invoice_address = False
        address_two.is_shipping_address = True
        address_two.save()
        registry.create_demo_data_relation(address_two)

    address_one.is_invoice_address = True
    address_one.is_shipping_address = True
    address_one.save()
    registry.create_demo_data_relation(address_one)
