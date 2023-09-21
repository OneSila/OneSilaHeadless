import strawberry_django
from strawberry import auto

from contacts.models import Company, Address, Person


@strawberry_django.filters.filter(Company, lookups=True)
class CompanyFilter:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@strawberry_django.filters.filter(Person, lookups=True)
class PersonFilter:
    first_name: auto
    last_name: auto
    email: auto
    company: CompanyFilter


@strawberry_django.filters.filter(Address, lookups=True)
class AddressFilter:
    company: CompanyFilter
    is_invoice_address: auto
    is_shipping_address: auto
