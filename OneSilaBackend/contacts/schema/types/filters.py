from core.schema.types.types import auto
from core.schema.types.filters import filter

from contacts.models import Company, Address, Person


@filter(Company)
class CompanyFilter:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@filter(Person)
class PersonFilter:
    first_name: auto
    last_name: auto
    email: auto
    company: CompanyFilter


@filter(Address)
class AddressFilter:
    company: CompanyFilter
    is_invoice_address: auto
    is_shipping_address: auto
