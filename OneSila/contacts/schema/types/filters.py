from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from contacts.models import Company, Address, Person, Supplier, \
    InvoiceAddress, ShippingAddress, Customer


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


@filter(Supplier)
class SupplierFilter:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto


@filter(Customer)
class CustomerFilter:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto


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


@filter(InvoiceAddress)
class InvoiceAddressFilter:
    company: CompanyFilter


@filter(ShippingAddress)
class ShippingAddressFilter:
    company: CompanyFilter
